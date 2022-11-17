from ast import literal_eval
from audioop import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from rest_framework import viewsets,status
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
# from cases.views import get_cases_from_cache
from core.models import comments,replies,priorities,contracts,documents
from .serializers import GroupSerializer, commentsSerializer,  repliesSerializer,prioritiesSerializer,contractsSerializer,documentsSerializer
from cases.models import LitigationCases
from activities.models import task,hearing
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import never_cache
from django.core.cache import cache
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.conf import settings
from django.utils import translation
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
from datetime import datetime, timedelta
from cases.utils import Calendar
from django.utils.safestring import mark_safe
import calendar
from datetime import date
from .permissions import MyPermission
import django_filters.rest_framework
from django.utils import timezone
# from rest_framework_tracking.mixins import LoggingMixin
## CALENDAR VIEW

# def get_comments_from_cache():
#     if 'all_comments' in cache:
#         return cache.get('all_comments')
#     else:
#         all_comments = comments.objects.all().order_by('-created_at')
#         cache.set('all_comments', all_comments)
#     return all_comments

# def get_replies_from_cache():
#     if 'all_replies' in cache:
#         return cache.get('all_replies')
#     else:
#         all_replies = replies.objects.all().order_by('-created_at')
#         cache.set('all_replies', all_replies)
#     return all_replies

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

@never_cache
def myhome(request):
    
    d = get_date(request.GET.get('month', None))
    pre_month = prev_month(d)
    nex_month = next_month(d)
    cal = Calendar(d.year, d.month)
    html_cal = cal.formatmonth(withyear=True)
    cases = LitigationCases.objects.all().order_by('-created_at')
    context = {
        'cases':cases,
        'calendar':mark_safe(html_cal),
        'prev_month':pre_month,
        'next_month':nex_month
        }
    return render(request, 'index.html', context=context)


@never_cache
def about(request):
    return render(request, 'about.html')


class GroupViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class commentsViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = comments.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = commentsSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.comments"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id','case_id','task_id','hearing_id']

    def create(self, request):
        comment = []
        serializer = []
        if "case_id" in request.data:
            req_case_id = request.data['case_id']
            comment = comments(id=None,case_id=req_case_id,comment=request.data['comment'],created_by=request.user)
            comment.save()
            LitigationCases.objects.get(id=req_case_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        # if "event_id" in request.data:
        #     event_id = request.data['event_id']
        #     event.objects.get(id=event_id).comments.add(comment)
        if "task_id" in request.data:
            req_task_id = request.data['task_id']
            comment = comments(id=None,task_id=req_task_id,comment=request.data['comment'],created_by=request.user)
            comment.save()
            task.objects.get(id=req_task_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        if "hearing_id" in request.data:
            req_hearing_id = request.data['hearing_id']
            comment = comments(id=None,hearing_id=req_hearing_id,comment=request.data['comment'],created_by=request.user)
            comment.save()
            hearing.objects.get(id=req_hearing_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        case = comments.objects.filter(id=pk)
        case.update(is_deleted=True)
        case.update(modified_by=request.user)
        case.update(modified_at=timezone.now())
        return Response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)

class repliesViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = replies.objects.all().order_by('-created_at').filter(is_deleted=False)
    serializer_class = repliesSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.replies"

    def create(self, request):
        if "reply" in request.data:
            reply = replies(id=None,reply=request.data['reply'],comment_id=int(request.data['comment_id']),created_by=request.user)
            reply.save()
            serializer = self.get_serializer(reply)
            if "comment_id" in request.data:
                comment_id = request.data['comment_id']
                comments.objects.get(id=comment_id).replies.add(reply)
                return Response(serializer.data,status=status.HTTP_201_CREATED)
            else:
                return Response({'error':'no comment id'},status=status.HTTP_201_CREATED)
        else:
            return Response({'error':'no reply'},status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        case = replies.objects.filter(id=pk)
        case.update(is_deleted=True)
        case.update(modified_by=request.user)
        case.update(modified_at=timezone.now())
        return Response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)

class prioritiesViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = priorities.objects.all().order_by('priority')
    serializer_class = prioritiesSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.priorities"


class contractsViewSet(viewsets.ModelViewSet):
    
    queryset = contracts.objects.all().order_by('-created_by').filter(is_deleted=False)
    serializer_class = contractsSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.contracts"

    def create(self,request):
            req_name = request.data['name']
            req_attachement = request.FILES.get('attachment')
            contract = contracts(id=None,name=req_name,attachment=req_attachement,created_by=request.user)
            contract.save()
            serializer = self.get_serializer(contract)
            return Response(serializer.data,status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        case = contracts.objects.filter(id=pk)
        case.update(is_deleted=True)
        case.update(modified_by=request.user)
        case.update(modified_at=timezone.now())
        return Response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)


    # def initial(self, request, *args, **kwargs):
    #     """
    #     Runs anything that needs to occur prior to calling the method handler.
    #     """
    #     self.format_kwarg = self.get_format_suffix(**kwargs)

    #     # Perform content negotiation and store the accepted info on the request
    #     neg = self.perform_content_negotiation(request)
    #     request.accepted_renderer, request.accepted_media_type = neg

    #     # Determine the API version, if versioning is in use.
    #     version, scheme = self.determine_version(request, *args, **kwargs)
    #     request.version, request.versioning_scheme = version, scheme

    #     # Ensure that the incoming request is permitted
    #     self.perform_authentication(request)
    #     self.check_permissions(request)
    #     self.check_throttles(request)

class documentsViewSet(viewsets.ModelViewSet):

    queryset = documents.objects.all().order_by('-created_by').filter(is_deleted=False)
    serializer_class = documentsSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.documents"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id','name','case_id']

    def create(self,request):
        req_name = None
        req_attachement = None
        req_case_id = None
        req_name = request.data['name']
        req_attachement = request.FILES.get('attachment')
        if "case_id" in request.data:
            req_case_id = request.data['case_id']
            if req_case_id != "":
                document = documents(id=None,name=req_name,case_id=req_case_id,attachment=req_attachement,created_by=request.user)
                document.save()
                case = get_object_or_404(LitigationCases,pk=req_case_id)
                case.documents.add(document)
            else:
                document = documents(id=None,name=req_name,attachment=req_attachement,created_by=request.user)
                document.save()
        else:
            document = documents(id=None,name=req_name,attachment=req_attachement,created_by=request.user)
            document.save()
        serializer = self.get_serializer(document)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        case = documents.objects.filter(id=pk)
        case.update(is_deleted=True)
        case.update(modified_by=request.user)
        case.update(modified_at=timezone.now())
        return Response(data={"detail":"Record is deleted"},status=status.HTTP_200_OK)

    # def initial(self, request, *args, **kwargs):
    #     """
    #     Runs anything that needs to occur prior to calling the method handler.
    #     """
    #     self.format_kwarg = self.get_format_suffix(**kwargs)

    #     # Perform content negotiation and store the accepted info on the request
    #     neg = self.perform_content_negotiation(request)
    #     request.accepted_renderer, request.accepted_media_type = neg

    #     # Determine the API version, if versioning is in use.
    #     version, scheme = self.determine_version(request, *args, **kwargs)
    #     request.version, request.versioning_scheme = version, scheme

    #     # Ensure that the incoming request is permitted
    #     self.perform_authentication(request)
    #     self.check_permissions(request)
    #     self.check_throttles(request)
        
        
            