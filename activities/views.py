from datetime import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response as rest_response
from django.contrib.contenttypes.models import ContentType
from accounts.models import User
from cases.models import LitigationCases, Folder
from core.classes import StandardResultsSetPagination, GetUniqueDictionaries, dict_item
from core.models import court, Status, priorities, Notification
from .models import task, hearing
from .serializers import taskSerializer, hearingSerializer, CombinedStatisticsSerializer, TaskStatisticsSerializer
from rest_framework.decorators import action
from django_celery_beat.models import PeriodicTask, PeriodicTasks, ClockedSchedule
import json
from activities.tasks import hearing_notification
from django.utils.dateparse import parse_date
from django.db.models import Count
from django.db.models import Q
from rest_framework.response import Response
from django.core.cache import cache


def filter_tasks(queryset, created_at_after=None, created_at_before=None, assignee_id=None):
    """Filter cases based on date range and assignee."""
    if created_at_after:
        queryset = queryset.filter(created_at__gte=parse_date(created_at_after))
    if created_at_before:
        queryset = queryset.filter(created_at__lte=parse_date(created_at_before))
    if assignee_id:
        queryset = queryset.filter(assignee=assignee_id)
    return queryset


def calculate_statistics(tasks):
    """Calculate various statistics from a queryset of cases."""
    total = tasks.count()
    status_counts = tasks.values('task_status__status').annotate(count=Count('id'))
    task_category_counts = tasks.values('task_category').annotate(count=Count('id'))

    status_dict = {item['task_status__status']: item['count'] for item in status_counts}
    task_category_dict = {item['task_category']: item['count'] for item in task_category_counts}

    return {
        'total': total,
        'status': status_dict,
        'category': task_category_dict,
    }


def all_tasks_query():
    cache_key = "tasks_queryset"
    cached_queryset = cache.get(cache_key)
    if cached_queryset:
        queryset = cached_queryset
    else:
        queryset = task.objects.all().order_by('-id').filter(is_deleted=False)
        cache.set(cache_key, queryset, timeout=600)
    return queryset

def all_hearings_query():
    cache_key = "hearings_queryset"
    cached_queryset = cache.get(cache_key)
    if cached_queryset:
        queryset = cached_queryset
    else:
        queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
        cache.set(cache_key, queryset, timeout=600)
    return queryset

class taskViewSet(viewsets.ModelViewSet):
    model = task
    queryset = task.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = taskSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticated,

    ]
    # perm_slug = "activities.task"
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]
    ordering_fields = [
        'created_at',
        'id',
        'modified_at'
    ]

    search_fields = ['=id', '@title']

    filterset_fields = [
        'title',
        'description',
        'case_id',
        'assignee',
        'task_category'
    ]

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()

        req_case_id = request.data.get('case_id')
        req_folder_id = request.data.get('folder_id')
        if req_case_id not in ('', None):
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            case.tasks.add(instance)
        if req_folder_id not in ('', None):
            folder = get_object_or_404(Folder, pk=req_folder_id)
            folder.tasks.add(instance)
        serializer = self.get_serializer(instance)
        task_cache_key = f"task_{instance.id}_queryset"
        cache.delete(task_cache_key)
        return rest_response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        tasks_cache_key = "tasks_queryset"
        cache.delete(tasks_cache_key)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        req_title = request.data.get('title')
        req_description = request.data.get('description')
        req_case_id = request.data.get('case_id')
        req_folder_id = request.data.get('folder_id')
        req_due_date = request.data.get('due_date')
        req_assign_date = request.data.get('assign_date')
        req_assignee = request.data.get('assignee')
        req_task_status = request.data.get('task_status')
        req_created_by = request.data.get('created_by')
        req_created_at = request.data.get('created_at')
        t_status, req_assignee_user = None, None
        if req_created_by not in ('', None):
            req_created_by = User.objects.get(
                username=request.data.get('created_by'))
        else:
            req_created_by = request.user
        if req_created_at in ('', None):
            req_created_at = timezone.now()
        if req_task_status not in ('', None):
            t_status = Status.objects.get(status=req_task_status)
        else:
            t_status = Status.objects.get(pk=1)
        if req_case_id not in ('', None):
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            tasks = task(id=None, title=req_title, description=req_description, task_status=t_status,
                         due_date=req_due_date, assign_date=req_assign_date, case_id=req_case_id,
                         created_by=req_created_by,
                         created_at=req_created_at)
            tasks.save()
            if req_assignee:
                notification_users_set = set(req_assignee)
                # if request.user.username in notification_users_set:
                #     notification_users_set.remove(request.user.username)
                # shared_with_users: list = []
                # for sh in notification_users_set:
                #     shu = User.objects.get(username=sh)
                #     tasks.assignee.add(shu.id)
                #     shared_with_users.append(shu)
                #     Notification.objects.create_notification(action='assign',
                #                                              content_type=ContentType.objects.get_for_model(tasks),
                #                                              object_id=tasks.id, object_name=tasks.title, action_by=request.user,
                #                                              user=shu,
                #                                              role='user')
                tasks.assignee.add(request.user)

            # if request.user != req_assignee_user:
            #     Notification.objects.create_notification(action='assign',
            #                                              content_type=ContentType.objects.get_for_model(tasks),
            #                                              object_id=tasks.id, action_by=request.user, user=req_assignee_user,
            #                                              role='user')
            serializer = self.get_serializer(tasks)
            case.tasks.add(tasks)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)
        if not req_folder_id in ('', None):
            folder = get_object_or_404(Folder, pk=req_folder_id)
            tasks = task(id=None, title=req_title, description=req_description, task_status=t_status,
                         due_date=req_due_date, assign_date=req_assign_date, folder_id=req_folder_id,
                         created_by=req_created_by,
                         created_at=req_created_at)
            tasks.save()
            if req_assignee:
                notification_users_set = set(req_assignee)
                if request.user.username in notification_users_set:
                    notification_users_set.remove(request.user.username)
                shared_with_users: list = []
                for sh in notification_users_set:
                    shu = User.objects.get(username=sh)
                    tasks.assignee.add(shu.id)
                    shared_with_users.append(shu)
                    Notification.objects.create_notification(action='assign',
                                                             content_type=ContentType.objects.get_for_model(tasks),
                                                             object_id=tasks.id, object_name=tasks.title,
                                                             action_by=request.user,
                                                             user=shu,
                                                             role='user')
                tasks.assignee.add(request.user)
            # if request.user != req_assignee_user:
            #     Notification.objects.create_notification(action='assign',
            #                                              content_type=ContentType.objects.get_for_model(tasks),
            #                                              object_id=tasks.id, action_by=request.user, user=req_assignee_user,
            #                                              role='user')
            serializer = self.get_serializer(tasks)
            folder.tasks.add(tasks)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            tasks = task(id=None, title=req_title, description=req_description, task_status=t_status,
                         due_date=req_due_date, assign_date=req_assign_date,
                         created_by=req_created_by,
                         created_at=req_created_at)
            tasks.save()
            if req_assignee:
                notification_users_set = set(req_assignee)
                if request.user.username in notification_users_set:
                    notification_users_set.remove(request.user.username)
                shared_with_users: list = []
                for sh in notification_users_set:
                    shu = User.objects.get(username=sh)
                    tasks.assignee.add(shu.id)
                    shared_with_users.append(shu)
                    Notification.objects.create_notification(action='assign',
                                                             content_type=ContentType.objects.get_for_model(tasks),
                                                             object_id=tasks.id, object_name=tasks.title,
                                                             action_by=request.user,
                                                             user=shu,
                                                             role='user')
                tasks.assignee.add(request.user)
            # if request.user != req_assignee_user:
            #     Notification.objects.create_notification(action='assign',
            #                                              content_type=ContentType.objects.get_for_model(tasks),
            #                                              object_id=tasks.id, action_by=request.user, user=req_assignee_user,
            #                                              role='user')
            serializer = self.get_serializer(tasks)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        current_task = task.objects.filter(id=pk)
        case_msg, folder_msg = '', ''
        tasks = task.objects.get(id=pk)
        notification_users: list = []
        managers_notifications = User.objects.filter(
            is_manager=True, email_notification=True)
        managers_users = [manager for manager in managers_notifications]
        shared_with_users = [shared_with for shared_with in tasks.assignee.all()]
        notification_users.extend(managers_users)
        notification_users.extend(shared_with_users)
        notification_users_set = set(notification_users)
        if request.user.username in notification_users_set:
            notification_users_set.remove(request.user.username)
        for notification_user in notification_users_set:
            Notification.objects.create_notification(action='delete',
                                                     content_type=ContentType.objects.get_for_model(tasks),
                                                     object_id=tasks.id, object_name=tasks.title,
                                                     action_by=request.user, user=notification_user,
                                                     role='manager')
        if tasks.case_id:
            case = get_object_or_404(LitigationCases, pk=tasks.case_id)
            case.tasks.remove(tasks)
            case_msg = f' and deleted from Case #{tasks.case_id}'
            tasks.case_id = None
            tasks.save()
        if tasks.folder_id:
            folder = get_object_or_404(Folder, pk=tasks.folder_id)
            folder.tasks.remove(tasks)
            folder_msg = f' and deleted from Folder #{tasks.folder_id}'
            tasks.folder_id = None
            tasks.save()
        current_task.update(
            is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        tasks_cache_key = "tasks_queryset"
        cache.delete(tasks_cache_key)
        return rest_response(data={"detail": f"Task is deleted {case_msg}{folder_msg}"}, status=status.HTTP_200_OK)

    def get_queryset(self):
        req_due_date = self.request.query_params.get('due_date')
        queryset = all_tasks_query()
        if req_due_date is not None:
            req_date = datetime.strptime(req_due_date, '%Y-%m').date()
            queryset = queryset.filter(
                due_date__year=req_date.year, due_date__month=req_date.month)
        current_user = self.request.user

        if current_user.is_superuser or current_user.is_manager:
            queryset = queryset
        elif current_user.is_cases_private_manager:
            cases = LitigationCases.objects.filter(case_category='Private')
            filter_query = Q(created_by=current_user) | Q(case_id__in=cases)
            queryset = queryset.filter(filter_query)
        elif current_user.is_cases_public_manager:
            cases = LitigationCases.objects.filter(case_category='Public')
            filter_query = Q(created_by=current_user) | Q(case_id__in=cases)
            queryset = queryset.filter(filter_query)
        else:
            filter_query = Q(assignee__exact=current_user) | Q(
                created_by__exact=current_user)
            queryset = queryset.filter(filter_query).distinct()
        return queryset

    def retrieve(self, request, pk=None):
        tasks_cache_key = "tasks_queryset"
        tasks_cached_queryset = cache.get(tasks_cache_key)
        task_cache_key = f"task_{pk}_queryset"
        task_cached_queryset = cache.get(task_cache_key)
        Task = None
        if tasks_cached_queryset:
            queryset = tasks_cached_queryset
        else:
            queryset = task.objects.filter(is_deleted=False).order_by('-created_by')
            cache.set(tasks_cache_key, queryset, timeout=600)
        current_user_id = request.user.id
        if not request.user.is_manager and not request.user.is_superuser:
            filter_query = Q(assignee__id__exact=current_user_id) | Q(
                created_by__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()

        if task_cached_queryset:
            Task = task_cached_queryset
        else:
            Task = get_object_or_404(queryset, pk=pk)
            cache.set(task_cache_key, Task, timeout=600)    
        serializer = self.get_serializer(Task)
        return rest_response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):

        serializer.save(modified_by=self.request.user)

    @action(methods=['get'], detail=False)
    def related_objects(self, request):
        cache_key = "tasks_objects"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            data = cached_queryset
            print('cached_queryset')
        else:
            tasks = self.get_queryset()
            cases: list = []
            assignees: list = []
            for task in tasks:
                if task.cases.all():
                    for case in task.cases.all():
                        cases.append(dict_item(case.id, case.name))
                if task.assignee.all():
                    for assignee in task.assignee.all():
                        assignees.append(dict_item(assignee.id, assignee.username))
                # if task.assignee:
                #     assignees.append(dict_item(task.assignee.id, task.assignee.username))
            cases_set = GetUniqueDictionaries(cases)
            assignees_set = GetUniqueDictionaries(assignees)
            data = {'cases': cases_set, 'assignees': assignees_set}
            cache.set(cache_key, data, timeout=600)
        return rest_response(status=status.HTTP_200_OK, data=data)

    @action(methods=['get'], detail=False, serializer_class=CombinedStatisticsSerializer)
    def statistics(self, request):
        statistics = []
        queryset = task.objects.filter(is_deleted=False)
        created_at_after = request.GET.get('created_at_after')
        created_at_before = request.GET.get('created_at_before')
        assignee_id = self.request.query_params.get('assignee')

        filtered_queryset = filter_tasks(queryset, created_at_after, created_at_before)

        statistics = []

        if assignee_id:
            cases = filtered_queryset.filter(assignee=assignee_id)
            assignee_statistics = calculate_statistics(cases)

            # Fetch and include assignee username
            try:
                assignee_username = User.objects.get(id=assignee_id).username
                assignee_statistics['assignee'] = assignee_username
                statistics.append(assignee_statistics)

                serializer = TaskStatisticsSerializer(assignee_statistics)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response({"detail": "Assignee not found."}, status=404)

        # Collect statistics for all assignees
        assignees = filtered_queryset.values_list('assignee', flat=True).distinct()
        for assignee_id in assignees:
            tasks = filtered_queryset.filter(assignee=assignee_id)
            assignee_statistics = calculate_statistics(tasks)

            try:
                assignee_username = User.objects.get(id=assignee_id).username
                assignee_statistics['assignee'] = assignee_username
                statistics.append(assignee_statistics)
            except User.DoesNotExist:
                continue

        # Calculate overall statistics
        overall_statistics = calculate_statistics(filtered_queryset)

        # Combine overall and by-assignee statistics
        combined_statistics = {
            'overall': overall_statistics,
            'by_assignee': statistics,
        }

        serializer = CombinedStatisticsSerializer(combined_statistics)
        return Response(serializer.data)


class hearingViewSet(viewsets.ModelViewSet):
    queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = hearingSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, ]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        #   FullWordSearchFilter,
    ]
    ordering_fields = ['created_at', 'id', 'modified_at']
    search_fields = ['@name', '=id', '@court__name']

    filterset_fields = [
        'name',
        'court',
        'assignee',
        'case_id'
    ]

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        req_case_id = request.data.get('case_id')
        req_folder_id = request.data.get('folder_id')
        if req_case_id not in ('', None):
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            case.hearing.add(instance)
        if req_folder_id not in ('', None):
            folder = get_object_or_404(Folder, pk=req_folder_id)
            folder.hearing.add(instance)
        serializer = self.get_serializer(instance)
        cache_key = "hearings_queryset"
        cache.delete(cache_key)
        return rest_response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        req_hearing_date = request.data.get('hearing_date')
        req_assignee = request.data.get('assignee')
        req_comments_by_lawyer = request.data.get('comments_by_lawyer')
        req_priority = request.data.get('priority')
        req_name = request.data.get('name')
        req_remind_me = request.data.get('remind_me')
        req_remind_date = request.data.get('remind_date')
        req_court = request.data.get('court')
        req_hearing_status = request.data.get('hearing_status')
        req_folder_id = request.data.get('folder_id')
        req_case_id = request.data.get('case_id')
        h_status, req_assignee_user = None, None
        if req_court not in ('', None):
            court_query = court.objects.filter(name=req_court)
            req_court = get_object_or_404(court_query)
        if req_priority not in ('', None):
            t_priority = priorities.objects.get(priority=req_priority)
        else:
            t_priority = priorities.objects.get(pk=1)
        # if req_assignee not in ('', None):
        #     req_assignee_user = User.objects.get(username=req_assignee)
        if req_hearing_status not in ('', None):
            h_status = Status.objects.get(status=req_hearing_status)
        else:
            h_status = Status.objects.get(pk=1)
        if req_case_id not in ('', None):
            notification_users_set = []
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            latest = True
            hearings = hearing(id=None, latest=latest, court=req_court, remind_me=req_remind_me,
                               hearing_status=h_status, name=req_name, case_id=req_case_id,
                               hearing_date=req_hearing_date, priority=t_priority, remind_date=req_remind_date,
                               comments_by_lawyer=req_comments_by_lawyer, created_by=request.user, )
            hearings.save()
            if req_assignee:
                notification_users_set = set(req_assignee)
                if request.user.username in notification_users_set:
                    notification_users_set.remove(request.user.username)
                shared_with_users: list = []
                for sh in notification_users_set:
                    shu = User.objects.get(username=sh)
                    hearings.assignee.add(shu.id)
                    shared_with_users.append(shu)
                    Notification.objects.create_notification(action='assign',
                                                             content_type=ContentType.objects.get_for_model(hearings),
                                                             object_id=hearings.id, object_name=hearings.name,
                                                             action_by=request.user,
                                                             user=shu,
                                                             role='user')
                    if req_remind_date:
                        execution_time = req_remind_date
                        schedule, created = ClockedSchedule.objects.get_or_create(clocked_time=execution_time)
                        PeriodicTask.objects.create(clocked=schedule,
                                                    one_off=True,
                                                    name=f'hearing: {hearings.name} user: {shu} date: {hearings.created_at}',
                                                    task='activities.tasks.hearing_notification',
                                                    args=json.dumps([hearings.id, shu.id]),
                                                    )
                hearings.assignee.add(request.user)
            serializer = self.get_serializer(hearings)
            case.hearing.all().update(latest=False)
            case.hearing.add(hearings)
            cache_key = "hearings_queryset"
            cache.delete(cache_key)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)
        if req_folder_id not in ('', None):
            folder = get_object_or_404(Folder, pk=req_folder_id)
            hearings = hearing(id=None, court=req_court, hearing_status=h_status, remind_me=req_remind_me,
                               name=req_name, folder_id=req_folder_id, hearing_date=req_hearing_date,
                               priority=t_priority, comments_by_lawyer=req_comments_by_lawyer,
                               remind_date=req_remind_date,
                               created_by=request.user, )
            hearings.save()
            if req_assignee:
                notification_users_set = set(req_assignee)
                if request.user.username in notification_users_set:
                    notification_users_set.remove(request.user.username)
                shared_with_users: list = []
                for sh in notification_users_set:
                    shu = User.objects.get(username=sh)
                    hearings.assignee.add(shu.id)
                    shared_with_users.append(shu)
                    Notification.objects.create_notification(action='assign',
                                                             content_type=ContentType.objects.get_for_model(hearings),
                                                             object_id=hearings.id, object_name=hearings.name,
                                                             action_by=request.user,
                                                             user=shu,
                                                             role='user')
                    if req_remind_date:
                        execution_time = req_remind_date
                        schedule, created = ClockedSchedule.objects.get_or_create(clocked_time=execution_time)
                        PeriodicTask.objects.create(clocked=schedule,
                                                    one_off=True,
                                                    name=f'hearing: {hearings.name} user: {shu} date: {hearings.created_at}',
                                                    task='activities.tasks.hearing_notification',
                                                    args=json.dumps([hearings.id, shu.id]),
                                                    )
                hearings.assignee.add(request.user)
            serializer = self.get_serializer(hearings)
            folder.hearing.add(hearings)
            cache_key = "hearings_queryset"
            cache.delete(cache_key)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            hearings = hearing(id=None, court=req_court, hearing_status=h_status, name=req_name,
                               remind_me=req_remind_me, priority=t_priority, hearing_date=req_hearing_date,
                               comments_by_lawyer=req_comments_by_lawyer, created_by=request.user,
                               remind_date=req_remind_date, )
            hearings.save()
            if req_assignee:
                notification_users_set = set(req_assignee)
                if request.user.username in notification_users_set:
                    notification_users_set.remove(request.user.username)
                shared_with_users: list = []
                for sh in notification_users_set:
                    shu = User.objects.get(username=sh)
                    hearings.assignee.add(shu.id)
                    shared_with_users.append(shu)
                    Notification.objects.create_notification(action='assign',
                                                             content_type=ContentType.objects.get_for_model(hearings),
                                                             object_id=hearings.id, object_name=hearings.name,
                                                             action_by=request.user,
                                                             user=shu,
                                                             role='user')
                    if req_remind_date:
                        execution_time = req_remind_date
                        schedule, created = ClockedSchedule.objects.get_or_create(clocked_time=execution_time)
                        PeriodicTask.objects.create(clocked=schedule,
                                                    one_off=True,
                                                    name=f'hearing: {hearings.name} user: {shu} date: {hearings.created_at}',
                                                    task='activities.tasks.hearing_notification',
                                                    args=json.dumps([hearings.id, shu.id]),
                                                    )
                hearings.assignee.add(request.user)
            serializer = self.get_serializer(hearings)
            cache_key = "hearings_queryset"
            cache.delete(cache_key)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        hearings = hearing.objects.filter(id=pk)
        hearings.update(is_deleted=True)
        hearings.update(modified_by=request.user)
        hearings.update(modified_at=timezone.now())
        case_msg, folder_msg = '', ''
        hear = hearing.objects.get(id=pk)
        notification_users: list = []
        managers_notifications = User.objects.filter(
            is_manager=True, email_notification=True)
        managers_users = [manager for manager in managers_notifications]
        shared_with_users = [shared_with for shared_with in hear.assignee.all()]
        notification_users.extend(managers_users)
        notification_users.extend(shared_with_users)
        notification_users_set = set(notification_users)
        if request.user.username in notification_users_set:
            notification_users_set.remove(request.user.username)
        for notification_user in notification_users_set:
            Notification.objects.create_notification(action='delete',
                                                     content_type=ContentType.objects.get_for_model(hear),
                                                     object_id=hear.id, object_name=hear.name, action_by=request.user,
                                                     user=notification_user,
                                                     role='manager')
        if hear.case_id:
            case = get_object_or_404(LitigationCases, pk=hear.case_id)
            case.hearing.remove(hear)
            case_msg = f' and deleted from Case #{hear.case_id}'
            hear.case_id = None
            hear.save()
        if hear.folder_id:
            folder = get_object_or_404(Folder, pk=hear.folder_id)
            folder.hearing.remove(hear)
            folder_msg = f' and deleted from Folder #{hear.folder_id}'
            hear.folder_id = None
            hear.save()
        cache_key = "hearings_queryset"
        cache.delete(cache_key)
        return rest_response(data={"detail": f"Hearing is deleted {case_msg}{folder_msg}"}, status=status.HTTP_200_OK)

    def get_queryset(self):
        req_hearing_date = self.request.query_params.get('hearing_date')
        cache_key = "hearings_queryset"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            queryset = cached_queryset
            print('cached_queryset')
        else:
            queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
            cache.set(cache_key, queryset, timeout=600)
        if req_hearing_date is not None:
            req_date = datetime.strptime(req_hearing_date, '%Y-%m').date()
            queryset = queryset.filter(
                hearing_date__year=req_date.year, hearing_date__month=req_date.month)
        current_user = self.request.user
        if current_user.is_superuser or current_user.is_manager:
            queryset = queryset
        elif current_user.is_cases_private_manager:
            cases = LitigationCases.objects.filter(case_category='Private')
            filter_query = Q(created_by=current_user) | Q(case_id__in=cases)
            queryset = queryset.filter(filter_query)
        elif current_user.is_cases_public_manager:
            cases = LitigationCases.objects.filter(case_category='Public')
            filter_query = Q(created_by=current_user) | Q(case_id__in=cases)
            queryset = queryset.filter(filter_query)
        else:
            filter_query = Q(assignee__exact=current_user) | Q(
                created_by__exact=current_user)
            queryset = queryset.filter(filter_query).distinct()
        return queryset

    def retrieve(self, request, pk=None):
        queryset = hearing.objects.order_by('-created_by')
        if request.user.is_manager or request.user.is_superuser:
            queryset = hearing.objects.all().order_by('-id')
        else:
            queryset = queryset.filter(created_by=request.user)
        hearings = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(hearings)
        return rest_response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        cache_key = "hearings_queryset"
        cache.delete(cache_key)
        serializer.save(modified_by=self.request.user)

    @action(methods=['get'], detail=False)
    def related_objects(self, request):
        cache_key = "hearings_objects"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            data = cached_queryset
            print('cached_queryset')
        else:
            hearings = self.get_queryset()
            cases: list = []
            courts: list = []
            assignees: list = []
            for hearing in hearings:
                if hearing.cases.all():
                    for case in hearing.cases.all():
                        cases.append(dict_item(case.id, case.name))
                if hearing.court:
                    courts.append(dict_item(hearing.court.id, hearing.court.name))
                if hearing.assignee.all():
                    for assignee in hearing.assignee.all():
                        assignees.append(dict_item(assignee.id, assignee.username))
                # if hearing.assignee:
                #     assignees.append(dict_item(hearing.assignee.id, hearing.assignee.username))
            cases_set = GetUniqueDictionaries(cases)
            courts_set = GetUniqueDictionaries(courts)
            assignees_set = GetUniqueDictionaries(assignees)
            data = {'cases': cases_set, 'courts': courts_set, 'assignees': assignees_set}
            cache.set(cache_key, data, timeout=600)
        return rest_response(status=status.HTTP_200_OK,
                             data=data)
