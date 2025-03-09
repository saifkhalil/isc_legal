import datetime
import json
from audioop import reverse
from datetime import datetime
from datetime import timedelta
import django_filters.rest_framework
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import ClockedSchedule, PeriodicTask
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from accounts.models import User
from accounts.models import User
from cases.permissions import Manager_SuperUser, Manager_SuperUser_Sub_Manager
from contract.models import Contract
from core.classes import StandardResultsSetPagination
from core.classes import dict_item, GetUniqueDictionaries
from core.models import Notification, priorities
from .forms import CaseForm
from .models import LitigationCases, stages, case_type, court, client_position, opponent_position, Folder, \
    ImportantDevelopment, Status, AdministrativeInvestigation, Notation, characteristic
from .permissions import MyPermission
from .serializers import LitigationCasesSerializer, stagesSerializer, case_typeSerializer, courtSerializer, \
    client_positionSerializer, opponent_positionSerializer, FoldersSerializer, \
    ImportantDevelopmentsSerializer, AdministrativeInvestigationsSerializer, NotationSerializer, \
    characteristicSerializer, LitigationCaseStatisticsSerializer, CombinedStatisticsSerializer
from core.mixins import CSVRendererMixin, CSVRendererMixin2
from django.utils.dateparse import parse_date
from django.core.cache import cache
from core.utils import LegalCache
from rest_framework.exceptions import NotFound

def manager_superuser_check(request):
    return Response(data={"detail": "انت غير مصرح بالمسح"}, status=status.HTTP_401_UNAUTHORIZED)
    current_user = User.objects.get(id=request.user.id)
    if not (current_user.is_manager or current_user.is_superuser):
        return Response(data={"detail": "انت غير مصرح بالمسح"}, status=status.HTTP_401_UNAUTHORIZED)


def case(request, case_id=None):
    instance = LitigationCases()
    if case_id:
        instance = get_object_or_404(LitigationCases, pk=case_id)
    else:
        instance = LitigationCases()

    form = CaseForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('cal:calendar'))
    return render(request, 'cases/case.html', {'form': form})


def filter_cases(queryset, created_at_after=None, created_at_before=None, assignee_id=None):
    """Filter cases based on date range and assignee."""
    if created_at_after:
        queryset = queryset.filter(created_at__gte=parse_date(created_at_after))
    if created_at_before:
        queryset = queryset.filter(created_at__lte=parse_date(created_at_before))
    if assignee_id:
        queryset = queryset.filter(assignee=assignee_id)
    return queryset


def calculate_statistics(cases):
    """Calculate various statistics from a queryset of cases."""
    total = cases.count()
    status_counts = cases.values('case_status__status').annotate(count=Count('id'))
    case_close_status_counts = cases.values('case_close_status').annotate(count=Count('id'))
    case_type_counts = cases.values('case_type__type').annotate(count=Count('id'))
    court_counts = cases.values('court__name').annotate(count=Count('id'))

    status_dict = {item['case_status__status']: item['count'] for item in status_counts}
    case_close_status_dict = {item['case_close_status']: item['count'] for item in case_close_status_counts}
    case_type_dict = {item['case_type__type']: item['count'] for item in case_type_counts}
    court_dict = {item['court__name']: item['count'] for item in court_counts}

    return {
        'total': total,
        'status': status_dict,
        'case_close_status': case_close_status_dict,
        'case_type': case_type_dict,
        'court': court_dict,
    }


class LitigationCasesViewSet(CSVRendererMixin2, viewsets.ModelViewSet):
    model = LitigationCases
    queryset = LitigationCases.objects.all().order_by('-created_by')
    serializer_class = LitigationCasesSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticated,
        Manager_SuperUser
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        #   FullWordSearchFilter,
    ]
    # perm_slug = "cases.LitigationCases"
    filterset_fields = ['id', 'Stage', 'case_type', 'case_status',
                        'case_category', 'assignee', 'court', 'start_time', 'characteristic', 'case_close_status']
    search_fields = ['@name', '@internal_ref_number', '=id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(LitigationCasesViewSet, self).dispatch(*args, **kwargs)

    def get_object(self):
        pk = self.kwargs.get("pk")
        obj = get_object_or_404(LitigationCases, pk=self.kwargs["pk"])
        current_user = self.request.user
        if current_user.is_manager or current_user.is_superuser:
            return obj
        elif current_user.is_cases_public_manager and obj.case_category == "Public":
            return obj
        elif current_user.is_cases_private_manager and obj.case_category == "Private":
            return obj
        elif (
            current_user in obj.shared_with.all()
            or obj.created_by == current_user
            or obj.assignee == current_user
        ):
            return obj
        else:
            raise NotFound(detail="Not found.")

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        notification_users: list = []
        req_name = request.data.get('name')
        req_description = request.data.get('description')
        req_case_category = request.data.get('case_category')
        req_judge = request.data.get('judge')
        req_detective = request.data.get('detective')
        req_court = request.data.get('court')
        req_client_position = request.data.get('client_position')
        req_opponent_position = request.data.get('opponent_position')
        req_stage = request.data.get('Stage')
        req_assignee = request.data.get('assignee')
        req_case_type = request.data.get('case_type')
        req_shared_with = request.data.get('shared_with')
        req_internal_ref_number = request.data.get('internal_ref_number')
        req_created_by = request.data.get('created_by')
        req_created_at = request.data.get('created_at')
        req_priority = request.data.get('priority')
        req_characteristic = request.data.get('characteristic')
        cache.delete("litigation_cases_queryset")
        cache.delete("litigation_cases_objects")
        if req_case_type not in (None, ''):
            req_case_type = case_type.objects.get(
                type=request.data.get('case_type'))
        else:
            req_case_type = None
        if req_court not in (None, ''):
            req_court = court.objects.get(name=request.data.get('court'))
        else:
            req_court = None
        if req_client_position not in (None, ''):
            req_client_position = client_position.objects.get(
                name=request.data.get('client_position'))
        else:
            req_client_position = None
        if req_opponent_position not in (None, ''):
            req_opponent_position = opponent_position.objects.get(
                position=request.data.get('opponent_position'))
        else:
            req_opponent_position = None
        if req_characteristic not in (None, ''):
            req_characteristic = characteristic.objects.get(
                name=request.data.get('characteristic'))
        else:
            req_characteristic = None

        if req_assignee not in ('', None):
            req_assignee = User.objects.get(
                username=request.data.get('assignee'))
        else:
            req_assignee = None
        if req_priority not in (None, ''):
            req_priority = priorities.objects.get(
                priority=request.data.get('priority'))
        else:
            req_priority = None
        if req_stage not in (None, ''):
            req_stage = stages.objects.get(name=request.data.get('Stage'))
        else:
            req_stage = None
        if req_created_by not in ('', None):
            req_created_by = User.objects.get(
                username=request.data.get('created_by'))
        else:
            req_created_by = request.user
        if req_created_at in ('', None):
            req_created_at = timezone.now()
        req_case_status = Status.objects.get(status='جديدة')
        req_start_time = request.data.get('start_time') if not request.data.get(
            'start_time') in ('', None) else None
        req_end_time = request.data.get('end_time') if not request.data.get(
            'end_time') in ('', None) else None
        cases = LitigationCases(
            id=None,
            name=req_name,
            description=req_description,
            case_category=req_case_category,
            judge=req_judge,
            detective=req_detective,
            case_type=req_case_type,
            court=req_court,
            client_position=req_client_position,
            opponent_position=req_opponent_position,
            assignee=req_assignee,
            internal_ref_number=req_internal_ref_number,
            priority=req_priority,
            Stage=req_stage,
            characteristic=req_characteristic,
            case_status=req_case_status,
            start_time=req_start_time,
            end_time=req_end_time,
            created_by=req_created_by,
            created_at=req_created_at
        )
        cases.save()
        notification_users.append(cases.assignee)
        if req_shared_with:
            shared_with_list: list = list(req_shared_with)
            shared_with_users: list = []
            for sh in shared_with_list:
                cases.shared_with.add(sh)
                shu = User.objects.get(id=sh)
                shared_with_users.append(shu)
            cases.shared_with.add(request.user)
            notification_users.extend(shared_with_users)
        else:
            cases.shared_with.add(request.user)
        managers_notifications = User.objects.filter(
            is_manager=True, email_notification=True)
        managers_users = [manager for manager in managers_notifications]
        notification_users.extend(managers_users)
        notification_users_set = set(notification_users)
        if request.user in notification_users_set:
            notification_users_set.remove(request.user)
        for notification_user in notification_users_set:
            Notification.objects.create_notification(action='create',
                                                     content_type=ContentType.objects.get_for_model(cases),
                                                     object_id=cases.id, action_by=request.user, user=notification_user,
                                                     object_name=cases.name,
                                                     role='manager')
        execution_time = cases.created_at + timedelta(days=30)
        schedule, created = ClockedSchedule.objects.get_or_create(clocked_time=execution_time)
        PeriodicTask.objects.create(clocked=schedule,
                                    one_off=True,
                                    name=f'{cases.name} {cases.created_at}',
                                    task='cases.tasks.late_case',
                                    args=json.dumps([cases.id, cases.created_by.id]),
                                    )
        serializer = self.get_serializer(cases)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        cache.delete("litigation_cases_queryset")
        cache.delete("litigation_cases_objects")
        instance = self.get_object()

        case = LitigationCases.objects.filter(id=pk)
        cases = LitigationCases.objects.get(id=pk)
        notification_users: list = []
        managers_notifications = User.objects.filter(
            is_manager=True, email_notification=True)
        managers_users = [manager for manager in managers_notifications]
        shared_with_users = [shared_with for shared_with in cases.shared_with.all()]
        notification_users.extend(managers_users)
        notification_users.extend(shared_with_users)
        notification_users_set = set(notification_users)
        if request.user in notification_users_set:
            notification_users_set.remove(request.user)
        for notification_user in notification_users_set:
            Notification.objects.create_notification(action='delete',
                                                     content_type=ContentType.objects.get_for_model(cases),
                                                     object_id=cases.id, object_name=cases.name, action_by=request.user,
                                                     user=notification_user,
                                                     role='manager')
        # notification = Notification(action='delete', content_type=content_type,
        #                             object_id=case_id, action_by=request.user)
        # notification.save()
        cases.tasks.all().update(is_deleted=True, modified_by=request.user,
                                 modified_at=timezone.now())
        cases.hearing.all().update(is_deleted=True, modified_by=request.user,
                                   modified_at=timezone.now())
        cases.paths.all().delete()
        case.update(is_deleted=True, modified_by=request.user,
                    modified_at=timezone.now())

        return Response(data={"detail": "تم مسح الدعوى بنجاح"}, status=status.HTTP_200_OK)

    def get_queryset(self):
        print('start LitigationCasesViewSet - get_queryset')
        internal_ref_number = self.request.query_params.get(
            'internal_ref_number')
        start_time = self.request.query_params.get('start_time', None)
        Stage = self.request.query_params.get('stage')
        Characteristic = self.request.query_params.get('characteristic')
        queryset = LitigationCases.objects.all().order_by('-created_by')
        current_user = self.request.user
        current_user_id = current_user.id
        # cuser = User.objects.get(id=current_user_id)
        is_manager = current_user.is_manager
        is_superuser = current_user.is_superuser
        is_cases_public_manager = current_user.is_cases_public_manager
        is_cases_private_manager = current_user.is_cases_private_manager
        if internal_ref_number is not None:
            queryset = queryset.filter(internal_ref_number=internal_ref_number)
        if Characteristic is not None:
            queryset = queryset.filter(characteristic=Characteristic)
        if start_time not in ('', None):
            req_date = datetime.strptime(start_time, '%Y-%m-%d').date()
            queryset = queryset.filter(start_time__year=req_date.year, start_time__month=req_date.month,
                                       start_time__day=req_date.day)
        if Stage not in ('', None):
            queryset = queryset.filter(Stage__id=Stage)
        filter_query = Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(assignee__id__exact=current_user_id)
        if is_manager or (is_cases_private_manager and is_cases_public_manager) or is_superuser:
            queryset = queryset
        elif is_cases_public_manager:
            filter_query = Q(case_category='Public') | Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(assignee__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()

        elif is_cases_private_manager:
            filter_query = Q(case_category='Private') | Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(assignee__id__exact=current_user_id)

            queryset = queryset.filter(filter_query).distinct()

        else:
            filter_query = Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(assignee__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        print('end LitigationCasesViewSet - get_queryset')
        return queryset

    def get_queryset_3(self):
        print("Start LitigationCasesViewSet - get_queryset")
        current_user = self.request.user
        # Retrieve query parameters
        params = self.request.query_params
        internal_ref_number = params.get("internal_ref_number")
        start_time = params.get("start_time")
        stage_id = params.get("stage")
        characteristic_id = params.get("characteristic")

        queryset = LitigationCases.objects.all().order_by('-created_by')
        normal_user_filter = (
            Q(shared_with=current_user)
            | Q(created_by=current_user)
            | Q(assignee=current_user)
        )

        queryset = queryset.filter(filters)

        # Fetch current user details
        current_user = self.request.user
        current_user_id = current_user.id

        # Access control logic
        user_filter = Q(shared_with__id=current_user_id) | Q(created_by__id=current_user_id) | Q(assignee__id=current_user_id)

        if internal_ref_number:
            queryset = queryset.filter(internal_ref_number=internal_ref_number)
        if characteristic_id:
            queryset = queryset.filter(characteristic_id=characteristic_id)
        if start_time:
            queryset = queryset.filter(start_time__date=start_time)
        if stage_id:
            queryset = queryset.filter(Stage_id=stage_id)
        if current_user.is_manager or current_user.is_superuser:
            return queryset

        if current_user.is_cases_public_manager:
            return queryset.filter(
                Q(case_category="Public") | normal_user_filter
            ).distinct()

        if current_user.is_cases_private_manager:
            return queryset.filter(
                Q(case_category="Private") | normal_user_filter
            ).distinct()

        queryset = queryset.filter(user_filter).distinct()

        # Optimize performance with prefetching related fields
        queryset = queryset.select_related("created_by", "assignee").prefetch_related("shared_with")

        print("End LitigationCasesViewSet - get_queryset")
        return queryset

    def perform_update(self, serializer):
        instance = self.get_object()
        serializer.save(modified_by=self.request.user)

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        cache.delete("litigation_cases_queryset")
        cache.delete("litigation_cases_objects")
        instance = self.get_object()
        if instance.case_status.is_completed or instance.case_status.is_done:
            instance.tasks.all().update(task_status=instance.case_status, modified_by=request.user,
                                        modified_at=timezone.now())
            instance.hearing.all().update(hearing_status=instance.case_status, modified_by=request.user,
                                          modified_at=timezone.now())
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def related_objects(self, request):
        cache_key = "litigation_cases_objects"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            data = cached_queryset
            print('cached_queryset')
        else:
            cases = self.get_queryset()
            Stage: list = []
            court: list = []
            case_type: list = []
            assignees: list = []
            for case in cases:
                if case.Stage:
                    Stage.append(dict_item(case.Stage.id, case.Stage.name))
                    if case.court:
                        court.append(dict_item(case.court.id, case.court.name))
                    if case.court:
                        case_type.append(dict_item(case.case_type.id, case.case_type.type))
                    if case.assignee:
                        assignees.append(dict_item(case.assignee.id, case.assignee.username))

            Stage_set = GetUniqueDictionaries(Stage)
            court_set = GetUniqueDictionaries(court)
            case_type_set = GetUniqueDictionaries(case_type)
            assignees_set = GetUniqueDictionaries(assignees)
            data={'Stage': Stage_set, 'court': court_set, 'case_type': case_type_set,'assignees': assignees_set}
            cache.set(cache_key, data, timeout=600)
        return Response(status=status.HTTP_200_OK,data=data)

    @action(methods=['get'], detail=False, serializer_class=CombinedStatisticsSerializer)
    def statistics(self, request):
        created_at_after = request.GET.get('created_at_after')
        created_at_before = request.GET.get('created_at_before')
        assignee_id = request.GET.get('assignee')
        statistics_type = request.GET.get('type', 'overall')  # Default to 'overall'

        # Initial queryset, filtered by deletion status
        queryset = LitigationCases.objects.filter(is_deleted=False)

        # Apply date filters
        filtered_queryset = filter_cases(queryset, created_at_after, created_at_before)

        combined_statistics = {}

        if statistics_type == 'overall':
            # Calculate overall statistics
            overall_statistics = calculate_statistics(filtered_queryset)
            combined_statistics['overall'] = overall_statistics
            combined_statistics['assignees'] = []

        elif statistics_type == 'assignees':
            # Collect statistics for all assignees
            statistics = []
            assignees = filtered_queryset.values_list('assignee', flat=True).distinct()
            for assignee_id in assignees:
                cases = filtered_queryset.filter(assignee=assignee_id)
                assignee_statistics = calculate_statistics(cases)

                try:
                    assignee_username = User.objects.get(id=assignee_id).username
                    assignee_statistics['assignee'] = assignee_username
                    statistics.append(assignee_statistics)
                except User.DoesNotExist:
                    continue

            combined_statistics['overall'] = None  # Indicate that overall statistics are not available
            combined_statistics['assignees'] = statistics

        elif statistics_type == 'assignee' and assignee_id:
            # Statistics for a specific assignee
            cases = filtered_queryset.filter(assignee=assignee_id)
            try:
                assignee_username = User.objects.get(id=assignee_id).username
                assignee_statistics = calculate_statistics(cases)
                assignee_statistics['assignee'] = assignee_username
                combined_statistics['overall'] = None  # Indicate that overall statistics are not available
                combined_statistics['assignees'] = [assignee_statistics]
            except User.DoesNotExist:
                return Response({"detail": "Assignee not found."}, status=404)

        else:
            return Response({"detail": "Invalid statistics type or missing assignee ID."}, status=400)

        serializer = CombinedStatisticsSerializer(combined_statistics)
        return Response(serializer.data)

class FoldersViewSet(viewsets.ModelViewSet):
    model = Folder
    queryset = Folder.objects.all().order_by('-created_by')
    serializer_class = FoldersSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticated,
        Manager_SuperUser_Sub_Manager
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        #   FullWordSearchFilter,
    ]
    # perm_slug = "folders.Folder"
    filterset_fields = ['id', 'record_type',
                        'folder_category', 'assignee', 'court']
    # word_fields = ('name','description')
    search_fields = ['@name', '@internal_ref_number', '=id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(FoldersViewSet, self).dispatch(*args, **kwargs)

    def destroy(self, request, pk=None):
        folder = Folder.objects.filter(id=pk)
        folders = Folder.objects.get(id=pk)
        folders.tasks.all().update(is_deleted=True, modified_by=request.user,
                                   modified_at=timezone.now())
        folders.hearing.all().update(is_deleted=True, modified_by=request.user,
                                     modified_at=timezone.now())
        folders.documents.all().update(
            is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        folder.update(is_deleted=True, modified_by=request.user,
                      modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    @action(detail=True)
    def get_comments(self, request, pk=None):
        comments = Folder.objects.filter(
            id=pk).comments.all().filter(is_deleted=False)
        return Response(comments, status=status.HTTP_200_OK)

    def get_queryset(self):
        internal_ref_number = self.request.query_params.get(
            'internal_ref_number')
        start_time = self.request.query_params.get('start_time')
        queryset = Folder.objects.all().order_by(
            '-created_by').filter(is_deleted=False)
        current_user_id = self.request.user.id
        cuser = User.objects.get(id=current_user_id)
        is_manager = cuser.is_manager
        is_superuser = cuser.is_superuser
        is_sub_manager = cuser.is_sub_manager
        if internal_ref_number is not None:
            queryset = queryset.filter(internal_ref_number=internal_ref_number)
        if start_time is not None:
            req_date = datetime.strptime(start_time, '%Y-%m').date()
            queryset = queryset.filter(
                start_time__year=req_date.year, start_time__month=req_date.month)
        if is_manager or is_superuser or is_sub_manager:
            queryset = queryset
        else:
            filter_query = Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(
                assignee__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        return queryset

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)


class AdministrativeInvestigationsFilter(filters.FilterSet):
    subject = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = AdministrativeInvestigation
        fields = ['subject', 'id', 'priority']


class AdministrativeInvestigationsViewSet(CSVRendererMixin2, viewsets.ModelViewSet):
    queryset = AdministrativeInvestigation.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = AdministrativeInvestigationsSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, Manager_SuperUser_Sub_Manager]
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AdministrativeInvestigationsFilter
    # filter_backends = [
    #     DjangoFilterBackend,
    #     SearchFilter,
    #     OrderingFilter,
    #     #   FullWordSearchFilter,
    # ]
    # filterset_fields = ['id', 'priority', ]
    # search_fields = ['=id', '@subject']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']
    perm_slug = "cases.AdministrativeInvestigation"

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(AdministrativeInvestigationsViewSet, self).dispatch(*args, **kwargs)

    def destroy(self, request, pk=None):
        AdministrativeInvestigations = AdministrativeInvestigation.objects.filter(id=pk)
        AdministrativeInvestigations.update(is_deleted=True)
        AdministrativeInvestigations.update(modified_by=request.user)
        AdministrativeInvestigations.update(modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

    def get_queryset(self):
        queryset = AdministrativeInvestigation.objects.all().order_by('-id').filter(is_deleted=False)
        current_user = self.request.user
        if current_user.is_superuser or current_user.is_manager or current_user.is_sub_manager:
            queryset = queryset
        else:
            filter_query = Q(assignee__exact=current_user) | Q(
                created_by__exact=current_user) | Q(shared_with__exact=current_user)
            queryset = queryset.filter(filter_query).distinct()
        return queryset


class NotationViewSet(CSVRendererMixin, viewsets.ModelViewSet):
    queryset = Notation.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = NotationSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, Manager_SuperUser_Sub_Manager]
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        #   FullWordSearchFilter,
    ]
    filterset_fields = ['id', 'priority', 'court', 'created_by', 'assignee']
    search_fields = ['@subject', '=id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    perm_slug = "cases.Notation"

    def destroy(self, request, pk=None):
        Notations = Notation.objects.filter(id=pk)
        Notations.update(is_deleted=True)
        Notations.update(modified_by=request.user)
        Notations.update(modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request):
        # request.data['created_by'] = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        notation = serializer.instance
        print('notation: ', serializer)
        notification_users: list = []
        managers_notifications = User.objects.filter(is_manager=True, )
        managers_users = [manager for manager in managers_notifications]
        shared_with_users = [shared_with for shared_with in notation.shared_with.all()]
        notification_users.extend(managers_users)
        notification_users.extend(shared_with_users)
        notification_users_set = set(notification_users)
        if request.user in notification_users_set:
            notification_users_set.remove(request.user)
        for notification_user in notification_users_set:
            Notification.objects.create_notification(action='delete',
                                                     content_type=ContentType.objects.get_for_model(notation),
                                                     object_id=notation.id, object_name=notation.subject,
                                                     action_by=request.user, user=notification_user,
                                                     role='manager')
        return Response(serializer.data)

    def get_queryset(self):
        queryset = Notation.objects.all().order_by('-id').filter(is_deleted=False)
        current_user = self.request.user
        if current_user.is_superuser or current_user.is_manager or current_user.is_sub_manager:
            queryset = queryset
        else:
            filter_query = Q(assignee__exact=current_user) | Q(
                created_by__exact=current_user) | Q(shared_with__exact=current_user)
            queryset = queryset.filter(filter_query).distinct()
        return queryset

    # def retrieve(self, request, pk=None):
    #     queryset = Notation.objects.filter(is_deleted=False).order_by('-created_by')
    #     current_user_id = request.user.id
    #     if not request.user.is_manager and not request.user.is_superuser:
    #         filter_query = Q(assignee__id__exact=current_user_id) | Q(
    #             created_by__id__exact=current_user_id)
    #         queryset = queryset.filter(filter_query).distinct()
    #     Notation = get_object_or_404(queryset, pk=pk)
    #     serializer = self.get_serializer(Notation)
    #     return rest_response(serializer.data, status=status.HTTP_200_OK)


class courtViewSet(viewsets.ModelViewSet):
    queryset = court.objects.all().order_by('name')
    serializer_class = courtSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.court"

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(courtViewSet, self).dispatch(*args, **kwargs)


class client_positionViewSet(viewsets.ModelViewSet):
    queryset = client_position.objects.all().order_by('-id')
    serializer_class = client_positionSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.client_position"

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(client_positionViewSet, self).dispatch(*args, **kwargs)


class opponent_positionViewSet(viewsets.ModelViewSet):
    queryset = opponent_position.objects.all().order_by('-id')
    serializer_class = opponent_positionSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.opponent_position"

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(opponent_positionViewSet, self).dispatch(*args, **kwargs)


class stagesViewSet(CSVRendererMixin, viewsets.ModelViewSet):
    queryset = stages.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = stagesSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.stages"
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        #   FullWordSearchFilter,
    ]
    filterset_fields = ['id', 'case_types__id']
    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(stagesViewSet, self).dispatch(*args, **kwargs)


class case_typeViewSet(viewsets.ModelViewSet):
    queryset = case_type.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = case_typeSerializer
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.case_type"

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(case_typeViewSet, self).dispatch(*args, **kwargs)


class characteristicViewSet(viewsets.ModelViewSet):
    queryset = characteristic.objects.all().order_by('-id')
    serializer_class = characteristicSerializer
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.characteristic"


class ImportantDevelopmentsViewSet(viewsets.ModelViewSet):
    queryset = ImportantDevelopment.objects.all().order_by(
        '-id').filter(is_deleted=False)
    serializer_class = ImportantDevelopmentsSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.ImportantDevelopment"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id', 'case_id', 'folder_id']

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(ImportantDevelopmentsViewSet, self).dispatch(*args, **kwargs)

    def create(self, request):
        ImportantDevelopments = []
        serializer = []
        req_case_id = request.data.get('case_id') if request.data.get('case_id') != '' else None
        req_folder_id = request.data.get('folder_id') if request.data.get('folder_id') != '' else None
        req_admin_id = request.data.get('admin_id') if request.data.get('admin_id') != '' else None
        req_notation_id = request.data.get('notation_id') if request.data.get('notation_id') != '' else None
        req_contract_id = request.data.get('contract_id') if request.data.get('contract_id') != '' else None
        if req_case_id not in ('', None) and req_folder_id not in ('', None):
            return Response({'error_message': "You can't send both case id and folder id in same request"},
                            status=status.HTTP_400_BAD_REQUEST)

        elif req_case_id not in ('', None):
            try:
                ImportantDevelopments = ImportantDevelopment(id=None, case_id=req_case_id, title=request.data['title'],
                                                             created_by=request.user)
                ImportantDevelopments.save()
                LitigationCases.objects.get(id=req_case_id).ImportantDevelopment.add(ImportantDevelopments)
                serializer = self.get_serializer(ImportantDevelopments)
            except Exception as error:
                return Response({'error_message': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        elif req_folder_id not in ('', None):
            try:
                ImportantDevelopments = ImportantDevelopment(id=None, folder_id=req_folder_id,
                                                             title=request.data['title'], created_by=request.user)
                ImportantDevelopments.save()
                Folder.objects.get(id=req_folder_id).ImportantDevelopment.add(ImportantDevelopments)
                serializer = self.get_serializer(ImportantDevelopments)
            except Exception as error:
                return Response({'error_message': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        elif req_admin_id not in ('', None):
            try:
                ImportantDevelopments = ImportantDevelopment(id=None, admin_id=req_admin_id,
                                                             title=request.data['title'], created_by=request.user)
                ImportantDevelopments.save()
                AdministrativeInvestigation.objects.get(id=req_admin_id).ImportantDevelopment.add(ImportantDevelopments)
                serializer = self.get_serializer(ImportantDevelopments)
            except Exception as error:
                return Response({'error_message': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        elif req_notation_id not in ('', None):
            try:
                ImportantDevelopments = ImportantDevelopment(id=None, notation_id=req_notation_id,
                                                             title=request.data['title'], created_by=request.user)
                ImportantDevelopments.save()
                Notation.objects.get(id=req_notation_id).ImportantDevelopment.add(ImportantDevelopments)
                serializer = self.get_serializer(ImportantDevelopments)
            except Exception as error:
                return Response({'error_message': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        elif req_contract_id not in ('', None):
            try:
                ImportantDevelopments = ImportantDevelopment(id=None, contract_id=req_contract_id,
                                                             title=request.data['title'], created_by=request.user)
                ImportantDevelopments.save()
                Contract.objects.get(id=req_contract_id).ImportantDevelopment.add(ImportantDevelopments)
                serializer = self.get_serializer(ImportantDevelopments)
            except Exception as error:
                return Response({'error_message': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error_message': 'You must enter case id or folder id'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        ImportantDevelopments = ImportantDevelopment.objects.filter(id=pk)
        ImportantDevelopments.update(is_deleted=True)
        ImportantDevelopments.update(modified_by=request.user)
        ImportantDevelopments.update(modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)
