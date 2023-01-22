from audioop import reverse
from django.shortcuts import render
from rest_framework import viewsets,status
from rest_framework import permissions
from rest_framework.response import Response
from .serializers import LitigationCasesSerializer,stagesSerializer,case_typeSerializer,courtSerializer,client_positionSerializer,opponent_positionSerializer,LitigationCasesEventSerializer,FoldersSerializer,ImportantDevelopmentsSerializer
from .models import LitigationCases,stages,case_type,court,client_position,opponent_position,LitigationCasesEvent,Folder,ImportantDevelopment
from rest_framework.authentication import TokenAuthentication,SessionAuthentication
from rest_framework.decorators import action
from activities.models import task,hearing
from django.db.models import Q
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
# from django.core.cache.backends.base import DEFAULT_TIMEOUT
from .forms import CaseForm
# CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
from .utils import Calendar
from .permissions import MyPermission
from accounts.models import User
import django_filters.rest_framework
from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count
from slick_reporting.views import SlickReportView
from slick_reporting.fields import SlickReportField
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
# from rest_framework_tracking.mixins import LoggingMixin
from rest_framework_word_filter import FullWordSearchFilter
# def get_cases_from_cache():
#     if 'all_cases' in cache:
#         return cache.get('all_cases')
#     else:
#         all_cases = LitigationCases.objects.all().order_by('-created_at')
#         cache.set('all_cases', all_cases)
#     return all_cases

# def get_companies_from_cache():
#     if 'all_companies' in cache:
#         return cache.get('all_companies')
#     else:
#         all_companies = company.objects.all().order_by('-id')
#         cache.set('all_companies', all_companies)
#     return all_companies

# def get_stages_from_cache():
#     if 'all_stages' in cache:
#         return cache.get('all_stages')
#     else:
#         all_stages = stages.objects.all().order_by('-id')
#         cache.set('all_stages', all_stages)
#     return all_stages

# def get_practice_areas_from_cache():
#     if 'all_practice_areas' in cache:
#         return cache.get('all_practice_areas')
#     else:
#         all_practice_areas = practice_area.objects.all().order_by('id')
#         cache.set('all_practice_areas', all_practice_areas)
#     return all_practice_areas

class TotalProductSales(SlickReportView):

    report_model = LitigationCases
    date_field = 'created_at'
    group_by = 'case_type__type'
    columns = ['case_type__type',
                SlickReportField.create(Count, 'id', name='sum__id') ]

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
    authentication_classes = [TokenAuthentication,SessionAuthentication]
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
    authentication_classes = [TokenAuthentication,SessionAuthentication]
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
    # perm_slug = "cases.LitigationCases"
    filterset_fields = ['id', 'Stage','case_type','case_category','assignee','court']
    # word_fields = ('name','description')
    search_fields = ['@name','@internal_ref_number','=id']
    ordering_fields = ['created_at', 'id','modified_at']
    ordering = ['-id']

    def destroy(self, request, pk=None):
        case = LitigationCases.objects.filter(id=pk)
        case.update(is_deleted=True)
        case.update(modified_by=request.user)
        case.update(modified_at=timezone.now())
        return Response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)

    # @action(detail=True)
    # def get_comments(self, request,pk=None):
    #     req_id =self.request.query_params.get('id')
    #     commments = LitigationCases.objects.filter(id=pk).comments.all()
    #     serializer = self.get_serializer(commments)
    #     return Response(commments, status=status.HTTP_200_OK)

    def get_queryset(self):
        internal_ref_number = self.request.query_params.get('internal_ref_number')
        start_time = self.request.query_params.get('start_time')
        Stage = self.request.query_params.get('stage')
        queryset = LitigationCases.objects.all().order_by('-created_by').filter(is_deleted=False)
        current_user_id = self.request.user.id
        cuser = User.objects.get(id=current_user_id)
        is_manager = cuser.is_manager
        if internal_ref_number is not None:
            queryset = queryset.filter(internal_ref_number=internal_ref_number)
        if start_time is not None:
            req_date = datetime.strptime(start_time, '%Y-%m').date()
            queryset = queryset.filter(start_time__year=req_date.year,start_time__month=req_date.month)
        if Stage is not None:
            queryset = queryset.filter(Stage__id=Stage)
        if is_manager:
            queryset = queryset
        else:
            filter_query = Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(assignee__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        return queryset


class FoldersViewSet(viewsets.ModelViewSet):
    
    model = Folder
    queryset = Folder.objects.all().order_by('-created_by')
    serializer_class = FoldersSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
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
    # perm_slug = "folders.Folder"
    filterset_fields = ['id', 'Stage','folder_type','folder_category','assignee','court']
    # word_fields = ('name','description')
    search_fields = ['@name','@internal_ref_number','=id']
    ordering_fields = ['created_at', 'id','modified_at']
    ordering = ['-id']
    
    def destroy(self, request, pk=None):
        folder = Folder.objects.filter(id=pk)
        folder.update(is_deleted=True)
        folder.update(modified_by=request.user)
        folder.update(modified_at=timezone.now())
        return Response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)

    @action(detail=True)
    def get_comments(self, request,pk=None):
        req_id =self.request.query_params.get('id')
        commments = Folder.objects.filter(id=pk).comments.all().filter(is_deleted=False)
        serializer = self.get_serializer(commments)
        return Response(commments, status=status.HTTP_200_OK)

    def get_queryset(self):
        internal_ref_number = self.request.query_params.get('internal_ref_number')
        start_time = self.request.query_params.get('start_time')
        Stage = self.request.query_params.get('stage')
        queryset = Folder.objects.all().order_by('-created_by').filter(is_deleted=False)
        current_user_id = self.request.user.id
        cuser = User.objects.get(id=current_user_id)
        is_manager = cuser.is_manager
        if internal_ref_number is not None:
            queryset = queryset.filter(internal_ref_number=internal_ref_number)
        if start_time is not None:
            req_date = datetime.strptime(start_time, '%Y-%m').date()
            queryset = queryset.filter(start_time__year=req_date.year,start_time__month=req_date.month)
        if Stage is not None:
            queryset = queryset.filter(Stage__id=Stage)
        if is_manager:
            queryset = queryset
        else:
            filter_query = Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(assignee__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        return queryset


# class companyViewSet(viewsets.ModelViewSet):

#     queryset = company.objects.all().order_by('-id')
#     serializer_class = companySerializer
#     permission_classes = [permissions.IsAuthenticated, MyPermission]
#     perm_slug = "cases.company"

class courtViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = court.objects.all().order_by('-id')
    serializer_class = courtSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.court"


class client_positionViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = client_position.objects.all().order_by('-id')
    serializer_class = client_positionSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.client_position"


class opponent_positionViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = opponent_position.objects.all().order_by('-id')
    serializer_class = opponent_positionSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.opponent_position"

class stagesViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = stages.objects.all().order_by('-id')
    serializer_class = stagesSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.stages"

class case_typeViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = case_type.objects.all().order_by('-id')
    serializer_class = case_typeSerializer
    authentication_classes = [TokenAuthentication,]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.case_type"

class ImportantDevelopmentsViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = ImportantDevelopment.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = ImportantDevelopmentsSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.ImportantDevelopment"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id','case_id']

    def create(self, request):
        ImportantDevelopments = []
        serializer = []
        if "case_id" in request.data:
            req_case_id = request.data['case_id']
            ImportantDevelopments = ImportantDevelopment(id=None,case_id=req_case_id,title=request.data['title'],created_by=request.user)
            ImportantDevelopments.save()
            LitigationCases.objects.get(id=req_case_id).ImportantDevelopment.add(ImportantDevelopments)
            serializer = self.get_serializer(ImportantDevelopments)
        # if "task_id" in request.data:
        #     req_task_id = request.data['task_id']
        #     ImportantDevelopments = ImportantDevelopment(id=None,task_id=req_task_id,title=request.data['title'],created_by=request.user)
        #     ImportantDevelopments.save()
        #     task.objects.get(id=req_task_id).ImportantDevelopment.add(ImportantDevelopments)
        #     serializer = self.get_serializer(ImportantDevelopments)
        # if "hearing_id" in request.data:
        #     req_hearing_id = request.data['hearing_id']
        #     ImportantDevelopments = ImportantDevelopment(id=None,hearing_id=req_hearing_id,title=request.data['title'],created_by=request.user)
        #     ImportantDevelopments.save()
        #     hearing.objects.get(id=req_hearing_id).ImportantDevelopment.add(ImportantDevelopments)
        #     serializer = self.get_serializer(ImportantDevelopments)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

    # def list(self, request):
    #     queryset = comments.objects.all().order_by('-id').filter(is_deleted=False)
    #     serializer = self.get_serializer(queryset)
    #     return Response(serializer.data,status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        ImportantDevelopments = ImportantDevelopment.objects.filter(id=pk)
        ImportantDevelopments.update(is_deleted=True)
        ImportantDevelopments.update(modified_by=request.user)
        ImportantDevelopments.update(modified_at=timezone.now())
        return Response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)