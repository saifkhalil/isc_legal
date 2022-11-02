from audioop import reverse
from django.shortcuts import render
from rest_framework import viewsets,status
from rest_framework import permissions
from rest_framework.response import Response
from .serializers import LitigationCasesSerializer,stagesSerializer,case_typeSerializer,courtSerializer,client_positionSerializer,opponent_positionSerializer
from .models import LitigationCases,stages,case_type,court,client_position,opponent_position
from rest_framework.authentication import TokenAuthentication,SessionAuthentication
from rest_framework.decorators import action
from activities.models import task
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
from core.permissions import MyPermission
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

class LitigationCasesViewSet(viewsets.ModelViewSet):
    
    queryset = LitigationCases.objects.all().order_by('-created_by')
    serializer_class = LitigationCasesSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.LitigationCases"

    # def list(self):
    #     queryset = queryset
    #     return queryset

    # def retrieve(self,pk=None):
    #     queryset = queryset.get(id=pk).values('id','name')
    #     return queryset

    def get_queryset(self):
        internal_ref_number = self.request.query_params.get('internal_ref_number')
        Stage = self.request.query_params.get('stage')
        queryset = LitigationCases.objects.all().order_by('-created_by')
        current_user_id = self.request.user.id
        is_manager = self.request.user.is_manager
        if internal_ref_number is not None:
            queryset = queryset.filter(internal_ref_number=internal_ref_number)
        if internal_ref_number is not None:
            queryset = queryset.filter(Stage__id=Stage)
        if is_manager:
            queryset = queryset
        else:
            queryset = queryset.filter(Q(shared_with__id__exact=current_user_id) | Q(shared_with__isnull=True))
        return queryset

# class companyViewSet(viewsets.ModelViewSet):

#     queryset = company.objects.all().order_by('-id')
#     serializer_class = companySerializer
#     permission_classes = [permissions.IsAuthenticated, MyPermission]
#     perm_slug = "cases.company"

class courtViewSet(viewsets.ModelViewSet):

    queryset = court.objects.all().order_by('-id')
    serializer_class = courtSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.court"


class client_positionViewSet(viewsets.ModelViewSet):

    queryset = client_position.objects.all().order_by('-id')
    serializer_class = client_positionSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.client_position"


class opponent_positionViewSet(viewsets.ModelViewSet):

    queryset = opponent_position.objects.all().order_by('-id')
    serializer_class = opponent_positionSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.opponent_position"

class stagesViewSet(viewsets.ModelViewSet):

    queryset = stages.objects.all().order_by('-id')
    serializer_class = stagesSerializer
    authentication_classes = [TokenAuthentication,SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.stages"

class case_typeViewSet(viewsets.ModelViewSet):
  
    queryset = case_type.objects.all().order_by('-id')
    serializer_class = case_typeSerializer
    authentication_classes = [TokenAuthentication,]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "cases.case_type"

