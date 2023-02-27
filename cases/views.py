from audioop import reverse
from datetime import datetime

import django_filters.rest_framework
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from slick_reporting.fields import SlickReportField
from slick_reporting.views import SlickReportView

from accounts.models import User
from cases.permissions import Manager_SuperUser
from core.classes import StandardResultsSetPagination
from core.models import priorities
from .forms import CaseForm
from .models import LitigationCases, stages, case_type, court, client_position, opponent_position, LitigationCasesEvent, \
    Folder, ImportantDevelopment, Status
from .permissions import MyPermission
from .serializers import LitigationCasesSerializer, stagesSerializer, case_typeSerializer, courtSerializer, \
    client_positionSerializer, opponent_positionSerializer, LitigationCasesEventSerializer, FoldersSerializer, \
    ImportantDevelopmentsSerializer


def manager_superuser_check(request):
    return Response(data={"detail": "انت غير مصرح بالمسح"}, status=status.HTTP_401_UNAUTHORIZED)
    current_user = User.objects.get(id=request.user.id)
    if not (current_user.is_manager or current_user.is_superuser):
        return Response(data={"detail": "انت غير مصرح بالمسح"}, status=status.HTTP_401_UNAUTHORIZED)


class TotalProductSales(SlickReportView):
    report_model = LitigationCases
    date_field = 'created_at'
    group_by = 'case_type__type'
    columns = ['case_type__type',
               SlickReportField.create(Count, 'id', name='sum__id')]

    chart_settings = [{
        'type': 'pie',
        'data_source': ['sum__id'],
        'plot_total': True,
        'title_source': 'case_type',
        'title': _('Detailed Columns'),

    }, ]


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


class LitigationCasesEventViewSet(viewsets.ReadOnlyModelViewSet):
    model = LitigationCasesEvent
    queryset = LitigationCasesEvent.objects.all().order_by('-created_by')
    serializer_class = LitigationCasesEventSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticated,
        #  MyPermission
    ]
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        #   FullWordSearchFilter,
    ]
    filterset_fields = ['id', ]


class LitigationCasesViewSet(viewsets.ModelViewSet):
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
    filterset_fields = ['id', 'Stage', 'case_type', 'case_category', 'assignee', 'court', 'start_time']
    search_fields = ['@name', '@internal_ref_number', '=id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    def create(self, request):
        req_name = request.data.get('name')
        req_description = request.data.get('description')
        req_case_category = request.data.get('case_category')
        req_judge = request.data.get('judge')
        req_detective = request.data.get('detective')
        req_case_type = case_type.objects.get(type=request.data.get('case_type'))
        req_court = court.objects.get(name=request.data.get('court'))
        req_client_position = client_position.objects.get(name=request.data.get('client_position'))
        req_opponent_position = opponent_position.objects.get(position=request.data.get('opponent_position'))
        req_assignee = User.objects.get(username=request.data.get('assignee'))
        req_shared_with = request.data.get('shared_with')
        req_internal_ref_number = request.data.get('internal_ref_number')
        req_priority = priorities.objects.get(priority=request.data.get('priority'))
        req_stage = stages.objects.get(name=request.data.get('Stage'))
        req_case_status = Status.objects.get(id=request.data.get('case_status'))
        req_start_time = datetime.strptime(request.data.get('start_time'), '%Y-%m-%d') if not request.data.get(
            'start_time') in ('', None) else None
        req_end_time = datetime.strptime(request.data.get('end_time'), '%Y-%m-%d') if not request.data.get(
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
            case_status=req_case_status,
            start_time=req_start_time,
            end_time=req_end_time,
            created_by=request.user,
        )
        cases.save()
        if req_shared_with:
            shared_with_list = list(req_shared_with)
            for sh in shared_with_list:
                cases.shared_with.add(sh)
            cases.shared_with.add(request.user)
        else:
            cases.shared_with.add(request.user)
        serializer = self.get_serializer(cases)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        case = LitigationCases.objects.filter(id=pk)
        cases = LitigationCases.objects.get(id=pk)
        cases.tasks.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        cases.hearing.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        cases.paths.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        case.update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        return Response(data={"detail": "تم مسح الدعوى بنجاح"}, status=status.HTTP_200_OK)

    def get_queryset(self):
        internal_ref_number = self.request.query_params.get('internal_ref_number')
        start_time = self.request.query_params.get('start_time', None)
        Stage = self.request.query_params.get('stage')
        queryset = LitigationCases.objects.all().order_by('-created_by').filter(is_deleted=False)
        current_user_id = self.request.user.id
        cuser = User.objects.get(id=current_user_id)
        is_manager = cuser.is_manager
        if internal_ref_number is not None:
            queryset = queryset.filter(internal_ref_number=internal_ref_number)
        if start_time not in ('', None):
            req_date = datetime.strptime(start_time, '%Y-%m-%d').date()
            queryset = queryset.filter(start_time__year=req_date.year, start_time__month=req_date.month,
                                       start_time__day=req_date.day)
        if Stage not in ('', None):
            queryset = queryset.filter(Stage__id=Stage)
        if is_manager:
            queryset = queryset
        else:
            filter_query = Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(
                assignee__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        return queryset


class FoldersViewSet(viewsets.ModelViewSet):
    model = Folder
    queryset = Folder.objects.all().order_by('-created_by')
    serializer_class = FoldersSerializer
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
    # perm_slug = "folders.Folder"
    filterset_fields = ['id', 'record_type', 'folder_category', 'assignee', 'court']
    # word_fields = ('name','description')
    search_fields = ['@name', '@internal_ref_number', '=id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    def destroy(self, request, pk=None):
        folder = Folder.objects.filter(id=pk)
        folders = Folder.objects.get(id=pk)
        folders.tasks.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        folders.hearing.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        folders.documents.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        folder.update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    @action(detail=True)
    def get_comments(self, request, pk=None):
        comments = Folder.objects.filter(id=pk).comments.all().filter(is_deleted=False)
        return Response(comments, status=status.HTTP_200_OK)

    def get_queryset(self):
        internal_ref_number = self.request.query_params.get('internal_ref_number')
        start_time = self.request.query_params.get('start_time')
        queryset = Folder.objects.all().order_by('-created_by').filter(is_deleted=False)
        current_user_id = self.request.user.id
        cuser = User.objects.get(id=current_user_id)
        is_manager = cuser.is_manager
        if internal_ref_number is not None:
            queryset = queryset.filter(internal_ref_number=internal_ref_number)
        if start_time is not None:
            req_date = datetime.strptime(start_time, '%Y-%m').date()
            queryset = queryset.filter(start_time__year=req_date.year, start_time__month=req_date.month)
        if is_manager:
            queryset = queryset
        else:
            filter_query = Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(
                assignee__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        return queryset


class courtViewSet(viewsets.ModelViewSet):
    queryset = court.objects.all().order_by('-id')
    serializer_class = courtSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.court"


class client_positionViewSet(viewsets.ModelViewSet):
    queryset = client_position.objects.all().order_by('-id')
    serializer_class = client_positionSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.client_position"


class opponent_positionViewSet(viewsets.ModelViewSet):
    queryset = opponent_position.objects.all().order_by('-id')
    serializer_class = opponent_positionSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.opponent_position"


class stagesViewSet(viewsets.ModelViewSet):
    queryset = stages.objects.all().order_by('-id')
    serializer_class = stagesSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.stages"


class case_typeViewSet(viewsets.ModelViewSet):
    queryset = case_type.objects.all().order_by('-id')
    serializer_class = case_typeSerializer
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.case_type"


class ImportantDevelopmentsViewSet(viewsets.ModelViewSet):
    queryset = ImportantDevelopment.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = ImportantDevelopmentsSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.ImportantDevelopment"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id', 'case_id']

    def create(self, request):
        ImportantDevelopments = []
        serializer = []
        if "case_id" in request.data:
            req_case_id = request.data['case_id']
            ImportantDevelopments = ImportantDevelopment(id=None, case_id=req_case_id, title=request.data['title'],
                                                         created_by=request.user)
            ImportantDevelopments.save()
            LitigationCases.objects.get(id=req_case_id).ImportantDevelopment.add(ImportantDevelopments)
            serializer = self.get_serializer(ImportantDevelopments)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        ImportantDevelopments = ImportantDevelopment.objects.filter(id=pk)
        ImportantDevelopments.update(is_deleted=True)
        ImportantDevelopments.update(modified_by=request.user)
        ImportantDevelopments.update(modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)
