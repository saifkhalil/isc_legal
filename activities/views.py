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
from accounts.models import User
from cases.models import LitigationCases, Folder
from core.classes import StandardResultsSetPagination
from core.models import court, Status
from .models import task, hearing
from .permissions import MyPermission
from .serializers import taskSerializer, hearingSerializer

class taskViewSet(viewsets.ModelViewSet):
    model = task
    queryset = task.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = taskSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticated,
        #  MyPermission
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
        'assignee'
    ]

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        req_case_id = request.data.get('case_id')
        req_folder_id = request.data.get('folder_id')
        if not req_case_id in ('', None):
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            case.tasks.add(instance)
        if not req_folder_id in ('', None):
            folder = get_object_or_404(Folder, pk=req_folder_id)
            folder.tasks.add(instance)
        serializer = self.get_serializer(instance)
        return rest_response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        req_title = request.data.get('title')
        req_description = request.data.get('description')
        req_case_id = request.data.get('case_id')
        req_folder_id = request.data.get('folder_id')
        req_due_date = request.data.get('due_date')
        req_assignee = request.data.get('assignee')
        req_task_status = request.data.get('task_status')
        t_status, req_assignee_user = None, None
        if not req_task_status in ('', None):
            t_status = Status.objects.get(pk=req_task_status)
        else:
            t_status = Status.objects.get(pk=1)
        if not req_assignee in ('', None):
            req_assignee_user = User.objects.get(username=req_assignee)
        if not req_case_id in ('', None):
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            tasks = task(id=None, title=req_title, description=req_description, task_status=t_status,
                         due_date=req_due_date, case_id=req_case_id, created_by=request.user,
                         assignee=req_assignee_user)
            tasks.save()
            serializer = self.get_serializer(tasks)
            case.tasks.add(tasks)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)
        if not req_folder_id in ('', None):
            folder = get_object_or_404(Folder, pk=req_folder_id)
            tasks = task(id=None, title=req_title, description=req_description, task_status=t_status,
                         due_date=req_due_date, folder_id=req_folder_id, created_by=request.user,
                         assignee=req_assignee_user)
            tasks.save()
            serializer = self.get_serializer(tasks)
            folder.tasks.add(tasks)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            tasks = task(id=None, title=req_title, description=req_description, task_status=t_status,
                         due_date=req_due_date, created_by=request.user, assignee=req_assignee_user)
            tasks.save()
            serializer = self.get_serializer(tasks)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        current_task = task.objects.filter(id=pk)
        case_msg, folder_msg = '', ''
        tasks = task.objects.get(id=pk)
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
        current_task.update(is_deleted=True, modified_by=request.user, modified_at=timezone.now())
        return rest_response(data={"detail": f"Task is deleted {case_msg}{folder_msg}"}, status=status.HTTP_200_OK)

    def get_queryset(self):
        req_due_date = self.request.query_params.get('due_date')
        queryset = task.objects.all().order_by('-id').filter(is_deleted=False)
        if req_due_date is not None:
            req_date = datetime.strptime(req_due_date, '%Y-%m').date()
            queryset = queryset.filter(due_date__year=req_date.year, due_date__month=req_date.month)
        return queryset

    def retrieve(self, request, pk=None):
        queryset = task.objects.filter(is_deleted=False).order_by('-created_by').filter(is_deleted=False)
        current_user_id = request.user.id
        if not request.user.is_manager:
            filter_query = Q(assignee__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        document = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(document)
        return rest_response(serializer.data, status=status.HTTP_200_OK)


class hearingViewSet(viewsets.ModelViewSet):
    queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = hearingSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    pagination_class = StandardResultsSetPagination
    perm_slug = "activities.hearing"
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
        return rest_response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        req_hearing_date = request.data.get('hearing_date')
        req_assignee = request.data.get('assignee')
        req_comments_by_lawyer = request.data.get('comments_by_lawyer')
        req_name = request.data.get('name')
        req_court = request.data.get('court')
        req_hearing_status = request.data.get('hearing_status')
        req_folder_id = request.data.get('folder_id')
        req_case_id = request.data.get('case_id')
        h_status, req_assignee_user = None, None
        if req_court not in ('', None):
            court_query = court.objects.filter(name=req_court)
            req_court = get_object_or_404(court_query)
        if req_assignee not in ('', None):
            req_assignee_user = User.objects.get(username=req_assignee)
        if req_hearing_status not in ('', None):
            h_status = Status.objects.get(status=req_hearing_status)
        else:
            h_status = Status.objects.get(pk=1)
        if req_case_id not in ('', None):
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            hearings = hearing(id=None, latest=True, court=req_court, hearing_status=h_status, name=req_name,
                               case_id=req_case_id, hearing_date=req_hearing_date,
                               comments_by_lawyer=req_comments_by_lawyer, created_by=request.user,
                               assignee=req_assignee_user)
            hearings.save()
            serializer = self.get_serializer(hearings)
            case.hearing.all().update(latest=False)
            case.hearing.add(hearings)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)
        if req_folder_id not in ('', None):
            folder = get_object_or_404(Folder, pk=req_folder_id)
            hearings = hearing(id=None, court=req_court, hearing_status=h_status, name=req_name,
                               folder_id=req_folder_id, hearing_date=req_hearing_date,
                               comments_by_lawyer=req_comments_by_lawyer, created_by=request.user,
                               assignee=req_assignee_user)
            hearings.save()
            serializer = self.get_serializer(hearings)
            folder.hearing.add(hearings)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            hearings = hearing(id=None, court=req_court, hearing_status=h_status, name=req_name,
                               hearing_date=req_hearing_date, comments_by_lawyer=req_comments_by_lawyer,
                               created_by=request.user, assignee=req_assignee_user)
            hearings.save()
            serializer = self.get_serializer(hearings)
            return rest_response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        hearings = hearing.objects.filter(id=pk)
        hearings.update(is_deleted=True)
        hearings.update(modified_by=request.user)
        hearings.update(modified_at=timezone.now())
        case_msg, folder_msg = '', ''
        hear = hearing.objects.get(id=pk)
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
        return rest_response(data={"detail": f"Hearing is deleted {case_msg}{folder_msg}"}, status=status.HTTP_200_OK)

    def get_queryset(self):
        req_hearing_date = self.request.query_params.get('hearing_date')
        queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
        if req_hearing_date is not None:
            req_date = datetime.strptime(req_hearing_date, '%Y-%m').date()
            queryset = queryset.filter(hearing_date__year=req_date.year, hearing_date__month=req_date.month)
        return queryset

    def retrieve(self, request, pk=None):
        queryset = hearing.objects.filter(is_deleted=False).order_by('-created_by')
        if not request.user.is_manager:
            queryset = queryset.filter(created_by=request.user)
        document = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(document)
        return rest_response(serializer.data, status=status.HTTP_200_OK)
