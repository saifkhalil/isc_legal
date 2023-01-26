from datetime import tzinfo
from django.http import HttpRequest
from django.shortcuts import render
from requests import Response
from rest_framework.response import Response as rest_response
from rest_framework import viewsets,status
from rest_framework import permissions
from django.utils import timezone
from cases.models import LitigationCases,Folder
from core.models import court,Status
from .serializers import taskSerializer,hearingSerializer
from .models import task,hearing
from rest_framework.authentication import TokenAuthentication ,SessionAuthentication
from django.core.cache import cache
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from .permissions import MyPermission
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
import django_filters.rest_framework
from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
# from rest_framework_tracking.mixins import LoggingMixin
from accounts.models import User
# CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

# def get_all_task_types_from_cache():
#     if 'all_task_types' in cache:
#         return cache.get('all_task_types')
#     else:
#         all_task_types = task_type.objects.all().order_by('-id')
#         cache.set('all_task_types', all_task_types)
#     return all_task_types

# def get_all_event_types_from_cache():
#     if 'all_event_types' in cache:
#         return cache.get('all_event_types')
#     else:
#         all_event_types = event_type.objects.all().order_by('-id')
#         cache.set('all_event_types', all_event_types)
#     return all_event_types

# def get_all_hearing_types_from_cache():
#     if 'all_hearing_types' in cache:
#         return cache.get('all_hearing_types')
#     else:
#         all_hearing_types = hearing_type.objects.all().order_by('-id')
#         cache.set('all_hearing_types', all_hearing_types)
#     return all_hearing_types

# def get_all_tasks_from_cache():
#     if 'all_tasks' in cache:
#         return cache.get('all_tasks')
#     else:
#         all_tasks = task.objects.all().order_by('-id')
#         cache.set('all_tasks', all_tasks)
#     return all_tasks

# def get_all_hearings_from_cache():
#     if 'all_hearings' in cache:
#         return cache.get('all_hearings')
#     else:
#         all_hearings = hearing.objects.all().order_by('id')
#         cache.set('all_hearings', all_hearings)
#     return all_hearings

# def get_all_events_from_cache():
#     if 'all_events' in cache:
#         return cache.get('all_events')
#     else:
#         all_events = event.objects.all().order_by('id')
#         cache.set('all_events', all_events)
#     return all_events

# Create your views here.
# class task_typeViewSet(viewsets.ModelViewSet):
#     queryset = task_type.objects.all().order_by('-id')
#     serializer_class = task_typeSerializer
#     authentication_classes = [TokenAuthentication,]
#     permission_classes = [permissions.IsAuthenticated, MyPermission]
#     perm_slug = "activities.task_type"

# class event_typeViewSet(viewsets.ModelViewSet):
#     queryset = event_type.objects.all().order_by('-id')
#     serializer_class = event_typeSerializer
#     authentication_classes = [TokenAuthentication,]
#     permission_classes = [permissions.IsAuthenticated, MyPermission]
#     perm_slug = "activities.event_type"

# class hearing_typeViewSet(viewsets.ModelViewSet):
#     queryset = hearing_type.objects.all().order_by('-id')
#     serializer_class = hearing_typeSerializer
#     authentication_classes = [TokenAuthentication,]
#     permission_classes = [permissions.IsAuthenticated, MyPermission]
#     perm_slug = "activities.hearing_type"

class taskViewSet(viewsets.ModelViewSet):
    model = task
    queryset = task.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = taskSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
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

    search_fields = ['=id','@title']

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
        if not req_case_id in ('',None):
            case = get_object_or_404(LitigationCases,pk=req_case_id)
            case.tasks.add(instance)
        if not req_folder_id in ('',None):
            folder = get_object_or_404(Folder,pk=req_case_id)
            folder.tasks.add(instance)
        serializer = self.get_serializer(instance)    
        return rest_response(serializer.data,status=status.HTTP_200_OK)

    def create(self,request):
        req_title = request.data.get('title')
        req_description = request.data.get('description')
        req_case_id = request.data.get('case_id')
        req_folder_id = request.data.get('folder_id')
        req_due_date = request.data.get('due_date')
        req_assignee = request.data.get('assignee')
        req_task_status = request.data.get('task_status')
        t_status,req_assignee_user = None,None
        if not req_task_status in ('',None):
            t_status = Status.objects.get(pk=req_task_status)
        else:
            t_status = Status.objects.get(pk=1)
        if not req_assignee in ('',None):
            req_assignee_user = User.objects.get(username=req_assignee)
        # if "comments" in request.data:
        #     req_comments = request.data["comments"]
        if not req_case_id in ('',None):
            case = get_object_or_404(LitigationCases,pk=req_case_id)
            tasks = task(id=None,title=req_title,description=req_description,task_status=t_status,due_date=req_due_date,case_id=req_case_id,created_by=request.user,assignee=req_assignee_user)
            tasks.save()
            serializer = self.get_serializer(tasks)    
            case.tasks.add(tasks)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)
        if not req_folder_id in ('',None):
            folder = get_object_or_404(Folder,pk=req_folder_id)
            tasks = task(id=None,title=req_title,description=req_description,task_status=t_status,due_date=req_due_date,folder_id=req_folder_id,created_by=request.user,assignee=req_assignee_user)
            tasks.save()
            serializer = self.get_serializer(tasks)    
            folder.tasks.add(tasks)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            tasks = task(id=None,title=req_title,description=req_description,task_status=t_status,due_date=req_due_date,created_by=request.user,assignee=req_assignee_user)
            tasks.save()
            serializer = self.get_serializer(tasks)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        case = task.objects.filter(id=pk)
        case.update(is_deleted=True)
        case.update(modified_by=request.user)
        case.update(modified_at=timezone.now())
        return rest_response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)

    def get_queryset(self):
        req_due_date = self.request.query_params.get('due_date')
        queryset = task.objects.all().order_by('-id').filter(is_deleted=False)
        if req_due_date is not None:
            req_date = datetime.strptime(req_due_date, '%Y-%m').date()
            queryset = queryset.filter(due_date__year=req_date.year,due_date__month=req_date.month)
        return queryset

    # def list(self, request):
    #     req_due_date = self.request.query_params.get('due_date')
    #     queryset = task.objects.all().filter(is_deleted=False).order_by('-created_by').filter(is_deleted=False)
    #     if req_due_date is not None:
    #         req_date = datetime.strptime(req_due_date, '%Y-%m').date()
    #         queryset = queryset.filter(due_date__year=req_date.year,due_date__month=req_date.month)
    #     current_user_id = request.user.id
    #     if request.user.is_manager == False:
    #         filter_query = Q(assignee__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id)
    #         queryset = queryset.filter(filter_query).distinct()
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #     serializer = self.get_serializer(page,many=True)
    #     return rest_response(serializer.data,status=status.HTTP_200_OK)


    def retrieve(self, request, pk=None):
        queryset = task.objects.filter(is_deleted=False).order_by('-created_by').filter(is_deleted=False)
        current_user_id = request.user.id
        if request.user.is_manager == False:
            filter_query = Q(assignee__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        document = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(document)
        return rest_response(serializer.data,status=status.HTTP_200_OK)

class hearingViewSet(viewsets.ModelViewSet):
    queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = hearingSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "activities.hearing" 
    filter_backends = [
        DjangoFilterBackend,
         SearchFilter,
          OrderingFilter,
        #   FullWordSearchFilter,
          ]
    ordering_fields = ['created_at', 'id','modified_at']
    search_fields = ['@name','=id','@court__name']

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
        if not req_case_id in ('',None):
            case = get_object_or_404(LitigationCases,pk=req_case_id)
            case.tasks.add(instance)
        if not req_folder_id in ('',None):
            folder = get_object_or_404(Folder,pk=req_case_id)
            folder.tasks.add(instance)
        serializer = self.get_serializer(instance)    
        return rest_response(serializer.data,status=status.HTTP_200_OK)

    def create(self,request):
        req_hearing_date = request.data.get('hearing_date')
        req_assignee = request.data.get('assignee')
        req_comments_by_lawyer = request.data.get('comments_by_lawyer')
        req_name = request.data.get('name')
        req_court = request.data.get('court')
        req_hearing_status = request.data.get('hearing_status')
        req_folder_id = request.data.get('folder_id')
        req_case_id = request.data.get('case_id')
        h_status,req_assignee_user = None,None
        if not req_court in ('',None):
            court_query = court.objects.filter(name=req_court)
            req_court = get_object_or_404(court_query)
        if not req_assignee in ('',None):
            req_assignee_user = User.objects.get(username=req_assignee)
        if not req_hearing_status in ('',None):
            h_status = Status.objects.get(status=req_hearing_status)
        else:
            h_status = Status.objects.get(pk=1)
        if not req_case_id in ('',None):
            case = get_object_or_404(LitigationCases,pk=req_case_id)
            hearings = hearing(id=None,court=req_court,hearing_status=h_status,name=req_name,case_id=req_case_id,hearing_date=req_hearing_date,comments_by_lawyer=req_comments_by_lawyer,created_by=request.user,assignee=req_assignee_user)
            hearings.save()
            serializer = self.get_serializer(hearings)    
            case.hearing.add(hearings)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)
        if not req_folder_id in ('',None):
            folder = get_object_or_404(Folder,pk=req_folder_id)
            hearings = hearing(id=None,court=req_court,hearing_status=h_status,name=req_name,folder_id=req_folder_id,hearing_date=req_hearing_date,comments_by_lawyer=req_comments_by_lawyer,created_by=request.user,assignee=req_assignee_user)
            hearings.save()
            serializer = self.get_serializer(hearings)    
            folder.hearing.add(hearings)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            hearings = hearing(id=None,court=req_court,hearing_status=h_status,name=req_name,hearing_date=req_hearing_date,comments_by_lawyer=req_comments_by_lawyer,created_by=request.user,assignee=req_assignee_user)
            hearings.save()
            serializer = self.get_serializer(hearings)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        case = hearing.objects.filter(id=pk)
        case.update(is_deleted=True)
        case.update(modified_by=request.user)
        case.update(modified_at=timezone.now())
        return rest_response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)

    def get_queryset(self):
        req_hearing_date = self.request.query_params.get('hearing_date')
        queryset = hearing.objects.all().order_by('-id').filter(is_deleted=False)
        if req_hearing_date is not None:
            req_date = datetime.strptime(req_hearing_date, '%Y-%m').date()
            queryset = queryset.filter(hearing_date__year=req_date.year,hearing_date__month=req_date.month)
        return queryset

    # def list(self, request):
    #     req_hearing_date = self.request.query_params.get('hearing_date')
    #     queryset = hearing.objects.all().filter(is_deleted=False).order_by('-created_by')
    #     if req_hearing_date is not None:
    #         req_date = datetime.strptime(req_hearing_date, '%Y-%m').date()
    #         queryset = queryset.filter(hearing_date__year=req_date.year,hearing_date__month=req_date.month)
    #     if request.user.is_manager == False:
    #         queryset = queryset.filter(created_by=request.user)
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #     serializer = self.get_serializer(page,many=True)
    #     return rest_response(serializer.data,status=status.HTTP_200_OK)


    def retrieve(self, request, pk=None):
        queryset = hearing.objects.filter(is_deleted=False).order_by('-created_by')
        if request.user.is_manager == False:
            queryset = queryset.filter(created_by=request.user)
        document = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(document)
        return rest_response(serializer.data,status=status.HTTP_200_OK)

    # def to_representation(self, instance):
    #         my_fields = {'id', 'name','hearing_date','assignee','court','comments_by_lawyer','case_id','case_name'}
    #         data = super().to_representation(instance)
    #         for field in my_fields:
    #             try:
    #                 if not data[field] or data[field] is None:
    #                     data[field] = "Saif"
    #             except KeyError:
    #                 pass
    #         return data
# class eventViewSet(viewsets.ModelViewSet):  
#     queryset = event.objects.all().order_by('id')
#     serializer_class = eventSerializer
#     authentication_classes = [TokenAuthentication,]
#     permission_classes = [permissions.IsAuthenticated, MyPermission]
#     perm_slug = "activities.event"