from datetime import tzinfo
from django.http import HttpRequest
from django.shortcuts import render
from requests import Response
from rest_framework.response import Response as rest_response
from rest_framework import viewsets,status
from rest_framework import permissions
from django.utils import timezone
from cases.models import LitigationCases
from core.models import court
from .serializers import taskSerializer,hearingSerializer
from .models import task,hearing
from rest_framework.authentication import TokenAuthentication ,SessionAuthentication
from django.core.cache import cache
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from core.permissions import MyPermission
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
import django_filters.rest_framework
from rest_framework.filters import SearchFilter, OrderingFilter
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
    
    queryset = task.objects.all().order_by('-id')
    serializer_class = taskSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "activities.task"

    def create(self,request):
        req_title = None
        req_description = None
        req_case_id = None
        req_due_date = None
        req_comments = None
        if "title" in request.data:
            req_title = request.data['title']
        if "description" in request.data:
            req_description = request.data['description']
        if "due_date" in request.data:
            req_due_date = request.data['due_date']
        if "comments" in request.data:
            req_comments = request.data["comments"]
        if "case_id" in request.data:
            req_case_id = request.data["case_id"]
            case = get_object_or_404(LitigationCases,pk=req_case_id)
            tasks = task(id=None,title=req_title,description=req_description,due_date=req_due_date,comments=req_comments,case_id=req_case_id,created_by=request.user)
            tasks.save()
            serializer = self.get_serializer(tasks)    
            case.tasks.add(tasks)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            tasks = task(id=None,title=req_title,description=req_description,due_date=req_due_date,comments=req_comments,created_by=request.user)
            tasks.save()
            serializer = self.get_serializer(tasks)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)

class hearingViewSet(viewsets.ModelViewSet):
    queryset = hearing.objects.all().order_by('-id')
    serializer_class = hearingSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "activities.hearing" 
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = '__all__'
    

    def create(self,request):
        req_hearing_date = None
        req_assignee = None
        req_comments_by_lawyer = None
        req_name = None
        req_court = None
        if "name" in request.data:
            req_name = request.data['name']
        if "court" in request.data:
            req_court = request.data['court']
            court_query = court.objects.filter(name=req_court)
            court_id = get_object_or_404(court_query)
        if "hearing_date" in request.data:
            req_hearing_date = request.data['hearing_date']
        if "assignee" in request.data:
            req_assignee = request.data["assignee"]
        if "comments_by_lawyer" in request.data:
            req_comments_by_lawyer = request.data["comments_by_lawyer"]
        if "case_id" in request.data:
            req_case_id = request.data["case_id"]
            case = get_object_or_404(LitigationCases,pk=req_case_id)
            hearings = hearing(id=None,court=court_id,name=req_name,case_id=req_case_id,hearing_date=req_hearing_date,comments_by_lawyer=req_comments_by_lawyer,created_by=request.user)
            hearings.save()
            serializer = self.get_serializer(hearings)    
            case.hearing.add(hearings)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            hearings = hearing(id=None,court=court_id,name=req_name,hearing_date=req_hearing_date,comments_by_lawyer=req_comments_by_lawyer,created_by=request.user)
            hearings.save()
            serializer = self.get_serializer(hearings)
            return rest_response(serializer.data,status=status.HTTP_201_CREATED)

# class eventViewSet(viewsets.ModelViewSet):  
#     queryset = event.objects.all().order_by('id')
#     serializer_class = eventSerializer
#     authentication_classes = [TokenAuthentication,]
#     permission_classes = [permissions.IsAuthenticated, MyPermission]
#     perm_slug = "activities.event"