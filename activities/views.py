from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import event_typeSerializer, eventSerializer, hearing_typeSerializer, task_typeSerializer,taskSerializer,hearingSerializer
from .models import task,event,hearing, task_type,event_type,hearing_type
from rest_framework.authentication import TokenAuthentication 

# Create your views here.
class task_typeViewSet(viewsets.ModelViewSet):
    queryset = task_type.objects.all().order_by('-id')
    serializer_class = task_typeSerializer
    permission_classes = [permissions.IsAuthenticated]

class event_typeViewSet(viewsets.ModelViewSet):
    queryset = event_type.objects.all().order_by('-id')
    serializer_class = event_typeSerializer
    permission_classes = [permissions.IsAuthenticated]

class hearing_typeViewSet(viewsets.ModelViewSet):
    queryset = hearing_type.objects.all().order_by('-id')
    serializer_class = hearing_typeSerializer
    permission_classes = [permissions.IsAuthenticated]

class taskViewSet(viewsets.ModelViewSet):
    queryset = task.objects.all().order_by('-id')
    serializer_class = taskSerializer
    permission_classes = [permissions.IsAuthenticated]

class hearingViewSet(viewsets.ModelViewSet):
    queryset = hearing.objects.all().order_by('id')
    serializer_class = hearingSerializer
    authentication_classes = [TokenAuthentication,]
    permission_classes = [permissions.AllowAny,]


class eventViewSet(viewsets.ModelViewSet):  
    queryset = event.objects.all().order_by('id')
    serializer_class = eventSerializer
    authentication_classes = [TokenAuthentication,]
    permission_classes = [permissions.AllowAny,]
