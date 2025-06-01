import json
from datetime import datetime
from urllib.parse import urlencode
from auditlog.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST, require_GET
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django_filters.rest_framework import DjangoFilterBackend
from pyasn1_modules.rfc2985 import contentType
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.response import Response as rest_response

from accounts.models import User
from cases.models import LitigationCases, Folder
from core.classes import StandardResultsSetPagination, GetUniqueDictionaries, dict_item
from core.models import court, Status, priorities, Notification
from .forms import TaskForm, HearingForm
from .models import hearing as hearing_model
from .models import task, hearing
from .models import task as task_model
from .serializers import taskSerializer, hearingSerializer, CombinedStatisticsSerializer, TaskStatisticsSerializer
from django.utils.translation import gettext_lazy as _

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
        cache.set(cache_key, queryset, None)
    return queryset

def all_hearings_query():
    cache_key = "hearings_queryset"
    cached_queryset = cache.get(cache_key)
    if cached_queryset:
        queryset = cached_queryset
    else:
        queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
        cache.set(cache_key, queryset, None)
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
            cache.set(tasks_cache_key, queryset, None)
        current_user_id = request.user.id
        if not request.user.is_manager and not request.user.is_superuser:
            filter_query = Q(assignee__id__exact=current_user_id) | Q(
                created_by__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()

        if task_cached_queryset:
            Task = task_cached_queryset
        else:
            Task = get_object_or_404(queryset, pk=pk)
            cache.set(task_cache_key, Task, None)
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
        else:
            tasks = self.get_queryset()
            cases: list = []
            assignees: list = []
            for task in tasks:
                if task.cases.all():
                    for case in task.cases.all():
                        cases.append(dict_item(case.id, case.name))
                if task.assignee.all():
                    for cassignee in task.assignee.all():
                        assignees.append(dict_item(cassignee.id, cassignee.username))
                # if task.assignee:
                #     assignees.append(dict_item(task.assignee.id, task.assignee.username))
            cases_set = GetUniqueDictionaries(cases)
            assignees_set = GetUniqueDictionaries(assignees)
            data = {'cases': cases_set, 'assignees': assignees_set}
            cache.set(cache_key, data, None)
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
        else:
            queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
            cache.set(cache_key, queryset, None)
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
                    for cassignee in hearing.assignee.all():
                        assignees.append(dict_item(cassignee.id, cassignee.username))
                # if hearing.assignee:
                #     assignees.append(dict_item(hearing.assignee.id, hearing.assignee.username))
            cases_set = GetUniqueDictionaries(cases)
            courts_set = GetUniqueDictionaries(courts)
            assignees_set = GetUniqueDictionaries(assignees)
            data = {'cases': cases_set, 'courts': courts_set, 'assignees': assignees_set}
            cache.set(cache_key, data, None)
        return rest_response(status=status.HTTP_200_OK,
                             data=data)

@login_required
def tasks_list(request):
    number_of_records = 10
    keywords = task_category = assignee = task_status = task_case = orderby = None
    task_category_set = assignee_set = task_status_set = cases_set = task_cases_set =  None

    if request.method == 'GET':
        # Clear filters and redirect if needed.
        if request.GET.get('clear'):
            for key in ['keywords', 'task_category', 'assignee', 'task_status', 'task_case', 'orderby', 'number_of_records']:
                request.session.pop(key, None)
            return redirect(request.path)

        # Retrieve filter parameters from GET or session.
        if 'keywords' in request.GET:
            keywords = request.GET.get('keywords')
            request.session['keywords'] = keywords  # Update session even if empty
        else:
            keywords = request.session.get('keywords', '')
        orderby = request.GET.get('orderby' ,'-modified_at') or request.session.get('orderby', '-modified_at')
        task_category = request.GET.get('task_category') or request.session.get('task_category',0)
        assignee = request.GET.get('assignee') or request.session.get('assignee',0)
        task_status = request.GET.get('task_status') or request.session.get('task_status',0)
        task_case = request.GET.get('task_case') or request.session.get('task_case',0)

        # Save parameters to session if provided.
        for key, value in (('keywords', keywords), ('task_category', task_category),
                           ('assignee', assignee), ('task_status', task_status),
                           ('task_case', task_case)):
            if value is not None:
                request.session[key] = value

        # Handle number_of_records.
        if request.GET.get('number_of_records'):
            try:
                number_of_records = int(request.GET.get('number_of_records'))
            except ValueError:
                number_of_records = 10
            request.session['number_of_records'] = number_of_records
        else:
            number_of_records = request.session.get('number_of_records', 10)

        # Build search query using Q objects.
        query = Q()
        if keywords:
            query |= Q(description__icontains=keywords)
            # Filter out words shorter than 2 characters.
            # query_words = [w for w in keywords.split() if len(w) >= 2]
            # for word in query_words:
            #     query |= Q(description__icontains=word)
        if task_category and task_category != '0':
            query &= Q(task_category=task_category)
        if task_status and task_status != '0':
            query &= Q(task_status_id=task_status)
        if assignee and assignee != '0':
            query &= Q(assignee__id=assignee)
        # Optionally, add status filtering if needed:
        if task_case and task_case != '0':
            query &= Q(case_id=task_case)

        # Get base queryset.
        tasks_qs = task_model.objects.filter(is_deleted=False).order_by('-created_by')

        # Retrieve filter dropdown data from cache or compute if not cached.
        task_key = "tasks_objects"
        cached_data = cache.get(task_key)
        if cached_data:
            task_status_set = cached_data.get('task_statuses')
            assignees_set = cached_data.get('assignees')
            task_cases_set = cached_data.get('task_cases')
        else:
            assignees = []
            task_statuses = []
            task_cases = []
            for ctask in tasks_qs:
                if ctask.task_status:
                    task_statuses.append(dict_item(ctask.task_status.id, ctask.task_status.status))
                if ctask.assignee.exists():
                    for cassignee in ctask.assignee.all():
                        assignees.append(dict_item(cassignee.id, cassignee.username))
                if ctask.case_id:
                    try:
                        case = LitigationCases.objects.get(pk=ctask.case_id)
                    except LitigationCases.DoesNotExist:
                        case = None
                    if case:
                        task_cases.append(dict_item(ctask.case_id, case.name))
            assignees_set = GetUniqueDictionaries(assignees)
            task_status_set = GetUniqueDictionaries(task_statuses)
            task_cases_set = GetUniqueDictionaries(task_cases)
            cached_data = {
                'assignees': assignees_set,
                'task_statuses': task_status_set,
                'task_cases': task_cases_set,
            }
            cache.set(task_key, cached_data, None)

        # Apply filters.
        tasks_qs = tasks_qs.filter(query)
    else:
        tasks_qs = task.objects.filter(is_deleted=False)
    tasks_qs = tasks_qs.order_by(orderby)
    # Set up pagination.
    paginator = Paginator(tasks_qs, number_of_records)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=2, on_ends=2)

    # Prepare session info for the template.
    session_info = {
        'number_of_records': number_of_records or 10,
        'keywords': keywords or '',
        'task_category': task_category or 0,
        'assignee': assignee or 0,
        'task_status': task_status or 0,
        'task_case': task_case or 0
    }

    # Build a filter query string to be used in pagination links.
    # Only include filter keys (exclude 'page').
    filter_params = {}
    for key in ['keywords', 'task_category', 'assignee', 'task_status', 'orderby', 'task_case', 'number_of_records']:
        value = request.session.get(key)
        if value:
            filter_params[key] = value
    filter_query = urlencode(filter_params)
    objs_count = tasks_qs.count()
    fields_to_show = [
        'id', 'title', 'task_status', 'assignee','cases', 'created_at', 'task_category', 'assign_date', 'due_date'
    ]

    headers = [
        _("Number"), _("Title"), _("Status"), _('Assignee'), _('Related Case'), _("Created At"), _('Category'), _("Start Date"), _('End Time'), _("Actions")
    ]
    filter_fields = [
        {
            "name": "keywords",
            "label": _("Search keywords"),
            "type": "text",
            "value": keywords,
        },
        {
            "name": "task_case",
            "label": _("Cases"),
            "type": "select",
            "value": task_case,
            "options": task_cases_set,
        },
        {
            "name": "task_status",
            "label": _("Status"),
            "type": "select",
            "value": task_status,
            "options": task_status_set,
        },
    ]
    obj_create = {'name': _('New Task'), 'url': 'task_create'}
    context = {
        'fields_to_show': fields_to_show,
        'headers': headers,
        'objs': page_obj,
        'objs_count': objs_count,
        'obj_view': 'task_view',
        'obj_edit': 'task_edit',
        'obj_delete': 'delete_task',
        'obj_create': obj_create,
        'page_range': page_range,
        'session': json.dumps(session_info),
        'filter_fields': filter_fields,
        'filter_query': filter_query,  # New variable for pagination links.
    }
    return render(request, 'objs_list.html', context)

@require_GET
def task_view(request, task_id=None,mode='view'):
    log = {}
    field_translations = {}
    OPERATION_TRANSLATIONS = {}
    instance = task()
    if task_id:
        instance = get_object_or_404(task, pk=task_id)
        if request.method == 'POST':
            if mode == 'edit':  # Allow editing only if mode is 'edit'
                form = TaskForm(request.POST, instance=instance, mode=mode)
                if form.is_valid():
                    instance = form.save(commit=False)  # Don't save yet, update fields first
                    instance.modified_by = request.user  # ✅ Correctly update modified_by
                    instance.modified_at = timezone.now()  # ✅ Correctly update modified_at
                    instance.save()  # Now save the instance with updated fields
                    return redirect('tasks_list')
            else:
                form = TaskForm(instance=instance, mode=mode)  # Read-only form
        else:
            form = TaskForm(instance=instance, mode=mode)
            if mode == 'view':
                OPERATION_TRANSLATIONS = {
                    'add': _('Add'),
                    'delete': _('Delete'),
                }
                field_translations = {
                    field.name: _(field.verbose_name)
                    for field in task._meta.fields
                }
                field_translations.update({
                    field.name: _(field.verbose_name)
                    for field in task._meta.many_to_many
                })
                log = LogEntry.objects.filter(content_type__model='task', object_id=instance.pk)
                for field in form.fields:
                    form.fields[field].widget.attrs['disabled'] = True  # Disable all fields
    else:
        mode = 'create'  # If no `case_id`, it's a new case
        instance = task()
        form = TaskForm(request.POST or None, instance=instance, mode=mode)
        if request.method == 'POST' and form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            instance.created_at = timezone.now()
            instance.save()
            return redirect('tasks_list')
    context = {
        'form': form,
        'obj': instance,
        'mode': mode,
        'logs': log,
        'obj_edit': 'task_edit',
        'objs_list': 'tasks_list',
        'new_path': 'new_task_path',
        'obj_new_comment':'new_task_comment',
        'field_translations': field_translations,
        'operation_translations': OPERATION_TRANSLATIONS,
    }
    return render(request, 'obj.html', context=context)

@require_POST
def new_task_comment(request, task_id=None):
    instance = get_object_or_404(task, pk=task_id)
    instance.comments.create(comment=request.POST.get('content'),created_by=request.user,created_at=timezone.now())
    return redirect('hearing_view',hearing_id=task_id)


@require_POST
def new_task_path(request, task_id=None):
    instance = get_object_or_404(task, pk=task_id)
    instance.paths.create(name=request.POST.get('name'))
    return redirect('case_view', case_id=task_id)

@require_POST
def delete_task(request, pk=None):
    instance = task.objects.get(pk=pk)
    if not (request.user.is_manager or request.user.is_superuser):
        return JsonResponse({'success': False, 'message':"You do not have permission to perform this action."},status=401)
    instance = get_object_or_404(task, pk=pk)
    instance.is_deleted = True
    instance.modified = timezone.now()
    # Assuming you have a field to record the modifying user:
    instance.modified_by = request.user
    instance.save()
    return JsonResponse({'success': True, 'message': _('Task has been deleted successfully.')},status=200)

@login_required
def hearings_list(request):
    number_of_records = 10
    keywords = court = assignee = hearing_status = hearing_case = orderby = None
    hearing_court_set = assignee_set = hearing_status_set = cases_set = None
    if request.method == 'GET':
        # Clear filters and redirect if needed.
        if request.GET.get('clear'):
            for key in ['keywords', 'court', 'assignee', 'hearing_status', 'hearing_case', 'number_of_records']:
                request.session.pop(key, None)
            return redirect(request.path)

        # Retrieve filter parameters from GET or session.
        if 'keywords' in request.GET:
            keywords = request.GET.get('keywords')
            request.session['keywords'] = keywords  # Update session even if empty
        else:
            keywords = request.session.get('keywords', '')
        court = request.GET.get('court') or request.session.get('court',0)
        orderby = request.GET.get('orderby', '-modified_at')
        assignee = request.GET.get('assignee') or request.session.get('assignee',0)
        hearing_status = request.GET.get('hearing_status') or request.session.get('hearing_status',0)
        hearing_case = request.GET.get('hearing_case') or request.session.get('hearing_case',0)
        # Save parameters to session if provided.
        for key, value in (('keywords', keywords), ('court', court),
                           ('assignee', assignee), ('hearing_status', hearing_status),
                           ('hearing_case', hearing_case)):
            if value is not None:
                request.session[key] = value
        # Handle number_of_records.
        if request.GET.get('number_of_records'):
            try:
                number_of_records = int(request.GET.get('number_of_records'))
            except ValueError:
                number_of_records = 10
            request.session['number_of_records'] = number_of_records
        else:
            number_of_records = request.session.get('number_of_records', 10)
        # Build search query using Q objects.
        query = Q()
        if keywords:
            query |= Q(name__icontains=keywords)
            # Filter out words shorter than 2 characters.
            # query_words = [w for w in keywords.split() if len(w) >= 2]
            # for word in query_words:
            #     query |= Q(description__icontains=word)
        if court and court != '0':
            query &= Q(court=court)
        if assignee and assignee != '0':
            query &= Q(assignee__id=assignee)
        if hearing_status and hearing_status != '0':
            query &= Q(hearing_status_id=hearing_status)
        # Optionally, add status filtering if needed:
        if hearing_case and hearing_case != '0':
            query &= Q(case_id=hearing_case)
        # Get base queryset.
        hearings_qs = hearing_model.objects.filter(is_deleted=False).order_by('-created_by')

        # Retrieve filter dropdown data from cache or compute if not cached.
        hearing_key = "hearings_objects"
        cached_data = cache.get(hearing_key)
        if cached_data:
            courts_set = cached_data.get('courts')
            assignees_set = cached_data.get('assignees')
            hearing_statuses_set = cached_data.get('hearing_statuses')
            hearing_case_set = cached_data.get('hearing_cases')
        else:
            courts = []
            assignees = []
            hearing_statuses = []
            hearing_cases = []
            for hearing in hearings_qs:
                if hearing.hearing_status:
                    hearing_statuses.append(dict_item(hearing.hearing_status.id, hearing.hearing_status.status))
                if hearing.court:
                    courts.append(dict_item(hearing.court.id, hearing.court.name))
                if hearing.assignee.exists():
                    for cassignee in hearing.assignee.all():
                        assignees.append(dict_item(cassignee.id, cassignee.username))
                if hearing.case_id:
                    hearing_cases.append(dict_item(hearing.case_id, LitigationCases.objects.get(pk=hearing.case_id).name))
            assignees_set = GetUniqueDictionaries(assignees)
            hearing_statuses_set = GetUniqueDictionaries(hearing_statuses)
            hearing_cases_set = GetUniqueDictionaries(hearing_cases)
            courts_set = GetUniqueDictionaries(courts)
            cached_data = {
                'assignees': assignees_set,
                'hearing_statuses': hearing_statuses_set,
                'hearing_cases': hearing_cases_set,
                'courts': courts_set,
            }
            cache.set(hearing_key, cached_data, None)
        # Apply filters.
        hearings_qs = hearings_qs.filter(query)
    else:
        hearings_qs = task.objects.filter(is_deleted=False)
    hearings_qs = hearings_qs.order_by(orderby)
    # Set up pagination.
    paginator = Paginator(hearings_qs, number_of_records)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=2, on_ends=2)
    # Prepare session info for the template.
    session_info = {
        'number_of_records': number_of_records or 10,
        'keywords': keywords or '',
        'court': court or 0,
        'assignee': assignee or 0,
        'hearing_status': hearing_status or 0,
        'hearing_case': hearing_case or 0
    }
    # Build a filter query string to be used in pagination links.
    # Only include filter keys (exclude 'page').
    filter_params = {}
    for key in ['keywords', 'court', 'assignee', 'hearing_status', 'hearing_case', 'number_of_records']:
        value = request.session.get(key)
        if value:
            filter_params[key] = value
    filter_query = urlencode(filter_params)
    objs_count = hearings_qs.count()
    fields_to_show = [
        'id', 'name', 'hearing_status', 'assignee', 'created_at', 'court','cases'
    ]

    headers = [
        _("Number"), _("Name"), _("Status"), _('Assignee'), _("Created At"), _("Court"), _('Related Case'), _("Actions")
    ]
    filter_fields = [
        {
            "name": "keywords",
            "label": _("Search keywords"),
            "type": "text",
            "value": keywords,
        },
        {
            "name": "cases",
            "label": _("Cases"),
            "type": "select",
            "value": hearing_case,
            "options": cases_set,
        },
    ]
    obj_create = {'name': _('New Hearing'), 'url': 'hearing_create'}
    context = {
        'fields_to_show': fields_to_show,
        'headers': headers,
        'objs': page_obj,
        'objs_count': objs_count,
        'obj_view': 'hearing_view',
        'obj_edit': 'hearing_edit',
        'obj_delete': 'delete_hearing',
        'obj_create': obj_create,
        'page_range': page_range,
        'session': json.dumps(session_info),
        'filter_fields': filter_fields,
        'filter_query': filter_query,  # New variable for pagination links.
    }
    return render(request, 'objs_list.html', context)

def hearing_view(request, hearing_id=None,mode='view'):
    log = {}
    field_translations = {}
    OPERATION_TRANSLATIONS = {}
    instance = hearing()
    if hearing_id:
        instance = get_object_or_404(hearing, pk=hearing_id)
        if request.method == 'POST':
            if mode == 'edit':  # Allow editing only if mode is 'edit'
                form = HearingForm(request.POST, instance=instance, mode=mode)
                if form.is_valid():
                    instance = form.save(commit=False)  # Don't save yet, update fields first
                    instance.modified_by = request.user  # ✅ Correctly update modified_by
                    instance.modified_at = timezone.now()  # ✅ Correctly update modified_at
                    instance.save()  # Now save the instance with updated fields
                    return redirect('hearings_list')
            else:
                form = HearingForm(instance=instance, mode=mode)  # Read-only form
        else:
            form = HearingForm(instance=instance, mode=mode)
            if mode == 'view':
                OPERATION_TRANSLATIONS = {
                    'add': _('Add'),
                    'delete': _('Delete'),
                }
                field_translations = {
                    field.name: _(field.verbose_name)
                    for field in hearing._meta.fields
                }
                field_translations.update({
                    field.name: _(field.verbose_name)
                    for field in hearing._meta.many_to_many
                })
                log = LogEntry.objects.filter(content_type__model='hearing', object_id=instance.pk)
                for field in form.fields:
                    form.fields[field].widget.attrs['disabled'] = True  # Disable all fields
    else:
        mode = 'create'  # If no `case_id`, it's a new case
        instance = hearing()
        form = HearingForm(request.POST or None, instance=instance, mode=mode)
        if request.method == 'POST' and form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            instance.created_at = timezone.now()
            instance.save()
            return redirect('hearings_list')
    context = {
        'form': form,
        'obj': instance,
        'mode': mode,
        'logs': log,
        'obj_edit': 'hearing_edit',
        'objs_list': 'hearings_list',
        'obj_new_comment':'new_hearing_comment',
        'field_translations': field_translations,
        'operation_translations': OPERATION_TRANSLATIONS,
    }
    return render(request, 'obj.html', context)

@require_POST
def delete_hearing(request, pk=None):
    instance = hearing.objects.get(pk=pk)
    if not (request.user.is_manager or request.user.is_superuser):
        return JsonResponse({'success': False, 'message':"You do not have permission to perform this action."},status=401)
    instance = get_object_or_404(hearing, pk=pk)
    instance.is_deleted = True
    instance.modified = timezone.now()
    # Assuming you have a field to record the modifying user:
    instance.modified_by = request.user
    instance.save()
    return JsonResponse({'success': True, 'message': _('Hearing has been deleted successfully.')},status=200)

@require_POST
def new_hearing_comment(request, hearing_id=None):
    instance = get_object_or_404(hearing, pk=hearing_id)
    instance.comments.create(comment=request.POST.get('content'),created_by=request.user,created_at=timezone.now())
    return redirect('hearing_view',hearing_id=hearing_id)


from django.http import HttpResponseRedirect
from formtools.wizard.views import SessionWizardView

def show_message_form_condition(wizard):
    # try to get the cleaned data of step 1
    cleaned_data = wizard.get_cleaned_data_for_step('0') or {}
    # check if the field ``leave_message`` was checked.
    return cleaned_data.get('leave_message', True)

class ContactWizard(SessionWizardView):

    def done(self, form_list, **kwargs):
        return render(self.request, 'base.html', {
            'form_data': [form.cleaned_data for form in form_list],
        })