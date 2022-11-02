from django.shortcuts import render
from rest_framework import viewsets,status
from rest_framework import permissions
from rest_framework.response import Response
from .serializers import LitigationCasesSerializer,stagesSerializer,practice_areaSerializer,companySerializer
from .models import LitigationCases,stages,practice_area,company
from rest_framework.authentication import TokenAuthentication 
from activities.models import event,task
from django.db.models import Q
# Create your views here.

class LitigationCasesViewSet(viewsets.ModelViewSet):
    
    queryset = LitigationCases.objects.all().order_by('-created_at')
    serializer_class = LitigationCasesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        internal_ref_number = self.request.query_params.get('internal_ref_number')
        Stage = self.request.query_params.get('stage')
        queryset = LitigationCases.objects.all().order_by('-created_at')
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

class companyViewSet(viewsets.ModelViewSet):

    queryset = company.objects.all().order_by('-id')
    serializer_class = companySerializer
    permission_classes = [permissions.IsAuthenticated]


class stagesViewSet(viewsets.ModelViewSet):

    queryset = stages.objects.all().order_by('-id')
    serializer_class = stagesSerializer
    permission_classes = [permissions.IsAuthenticated]

class practice_areaViewSet(viewsets.ModelViewSet):
  
    queryset = practice_area.objects.all().order_by('id')
    serializer_class = practice_areaSerializer
    authentication_classes = [TokenAuthentication,]
    permission_classes = [permissions.IsAuthenticated,]

