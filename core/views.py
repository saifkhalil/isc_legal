import calendar
import json
import re
from datetime import date
from datetime import datetime, timedelta
from urllib.parse import urlencode
import django_filters.rest_framework
from auditlog.models import LogEntry
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.urls import translate_url
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import activate
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django_filters.rest_framework import DjangoFilterBackend
from pghistory.models import Events
from rest_framework import generics as rest_framework_generics
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from accounts.models import User
from activities.models import task, hearing
from cases.models import LitigationCases, Folder, AdministrativeInvestigation, Notation
from cases.permissions import Manager_SuperUser
from cases.utils import Calendar
from contract.models import Contract
from core.classes import StandardResultsSetPagination
from core.models import comments, replies, priorities, contracts, documents, Status, Path, Notification
from rest_api import generics
from rest_api.api_view_mixins import ExternalObjectAPIViewMixin
from .permissions import MyPermission
from .serializers import (
    EventsSerializer, GroupSerializer, commentsSerializer, repliesSerializer, prioritiesSerializer,
    contractsSerializer, documentsSerializer, StatusSerializer, NotificationSerializer, LogEntrySerializer,
    YourMPTTModelSerializer
)
from .serializers import (
    PathDocumentAddSerializer, PathDocumentRemoveSerializer,
    PathSerializer
)
from django.utils.translation import gettext_lazy as _

def service_worker_view(request):
    sw_path = settings.STATIC_ROOT.joinpath("css/service-worker.js") # This should be your path to service-worker.js
    response = HttpResponse(open(sw_path).read(),
    content_type='application/javascript')
    response.headers['Service-Worker-Allowed'] = '/'
    return response

def index(request):

    return render(request, 'index.html')

def setCache(key,query):
    cache_data = cache.get(key)
    if cache_data:
        result = cache_data
    else:
        result = query
        cache.set(key, result, timeout=None)
    return result

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.month) + '&year=' + str(prev_month.year)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.month) + '&year=' + str(next_month.year)
    return month

def years_list() -> list:
    current_year = timezone.now().year +1
    years: list[int] = [year for year in range(2020, current_year)]
    return years

def month_list():
    months = [
        {'number':1,'name': _("January")},
        {'number':2,'name': _("February")},
        {'number':3,'name': _("March")},
        {'number':4,'name': _("April")},
        {'number':5,'name': _("May")},
        {'number':6,'name': _("June")},
        {'number':7,'name': _("July")},
        {'number':8,'name': _("August")},
        {'number':9,'name': _("September")},
        {'number':10,'name': _("October")},
        {'number':11,'name': _("November")},
        {'number':12,'name': _("December")},
    ]
    return months

def get_date(month,year):
    if month and year:
        return date(int(year), int(month), day=1)
    return datetime.today()

@never_cache
@login_required
def myhome(request):
    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    d = get_date(month,year)
    pre_month = prev_month(d)
    nex_month = next_month(d)
    cal = Calendar(d.year, d.month)
    html_cal = cal.formatmonth(withyear=True)
    context = {
        'calendar': mark_safe(html_cal),
        'prev_month': pre_month,
        'next_month': nex_month,
        'selected_year':d.year,
        'selected_month':d.month,
        'years':years_list(),
        'months':month_list(),
    }
    return render(request, 'index.html', context=context)


@login_required
def set_theme_color(request):
    if request.method == "POST":
        theme_color = request.POST.get("theme_color")
        if request.user.is_authenticated:
            request.user.theme_color = theme_color
            request.user.save()

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def set_animation(request):
    if request.method == "POST":
        animation = True if request.POST.get("animation") == 'on' else False
        print(f'{request.POST}')
        if request.user.is_authenticated:
            request.user.enable_transition = animation
            request.user.save()

    return redirect(request.META.get("HTTP_REFERER", "/"))

@login_required
def set_language(request):
    if request.method == "POST":
        language = request.POST.get("language")

        if language:
            request.session["django_language"] = language  # Store in session
            activate(language)  # Apply new language

            # Update user's language preference
            if request.user.is_authenticated:
                request.user.language = language
                request.user.save()

            # Get current request URL
            old_url = request.META.get("HTTP_REFERER", "/")
            print(f'old_url: {old_url}')

            # Try using translate_url first
            new_url = translate_url(old_url, language)

            # If translate_url fails, manually replace language prefix while keeping full path
            if not new_url or new_url == old_url:
                match = re.match(r'http://[^/]+/(en|ar)(/.*)?$', old_url)  # Detect language prefix
                if match:
                    new_url = f'/{language}{match.group(2) or "/"}'  # Replace prefix & keep path
                else:
                    new_url = f'/{language}/'  # Default to root with language
            return redirect(new_url)

    return redirect(request.META.get("HTTP_REFERER", "/"))  # Fallback redirect

@never_cache
@login_required
def about(request):
    return render(request, 'about.html')

def load_more_notifications(request):
    """Load more notifications via AJAX for infinite scroll."""
    page = int(request.GET.get("page", 1))  # Get current page number
    per_page = 10  # Number of notifications per page

    notifications = Notification.objects.filter(user=request.user).order_by("-action_at")
    paginator = Paginator(notifications, per_page)

    if page > paginator.num_pages:
        return JsonResponse({"notifications": [], "has_more": False})

    notification_list = [
        {
            "id": notification.id,
            "action":"أنشأ" if notification.action =="create" else "حدث" if notification.action == "edit" else "حذف",
            "action_by": notification.action_by.username if notification.action_by else "System",
            "object_name": notification.object_name[0:20],
            "content_type": notification.content_type.model,
            "timestamp": notification.action_at.strftime("%Y-%m-%d %H:%M"),
            "is_read":notification.is_read,
        }
        for notification in paginator.page(page).object_list
    ]

    return JsonResponse({"notifications": notification_list, "has_more": page < paginator.num_pages})

def read_all_notifications(request):
    user = request.user
    Notification.objects.filter(user=user).order_by("-action_at").update(is_read=True)
    return JsonResponse({'success': True, 'message': 'All Notification has been read successfully.'},status=200)

def read_notification(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True, 'message': 'Notification has been read successfully.'},status=200)

def delete_all_notifications(request):
    user = request.user
    Notification.objects.filter(user=user).order_by("-action_at").update(is_deleted=True)
    return JsonResponse({'success': True, 'message': 'All Notification has been deleted successfully.'},status=200)

def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    notification.is_deleted = True
    notification.save()
    return JsonResponse({'success': True, 'message': 'Notification has been deleted successfully.'},status=200)

def notifications(request):
    return render(request, 'notification.html')

class LogsViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = StandardResultsSetPagination
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]

    ordering_fields = ['timestamp', ]
    ordering = ['-timestamp']

    def get_queryset(self):
        queryset = setCache('LogEntry_queryset',LogEntry.objects.all())
        req_model = self.request.query_params.get('model', None)
        req_object_id = self.request.query_params.get('object_id', None)
        if req_model not in (None, ''):
            queryset = queryset.filter(content_type__model=req_model)
        if req_object_id not in (None, ''):
            queryset = queryset.filter(object_id=req_object_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(actor=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

class GroupViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class commentsViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = comments.objects.all().order_by('-id').filter(is_deleted=False)
    serializer_class = commentsSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    pagination_class = StandardResultsSetPagination
    perm_slug = "core.comments"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id', 'case_id', 'task_id', 'hearing_id', 'contract_id']

    def create(self, request):
        comment = []
        serializer = []
        req_case_id = request.data.get('case_id')
        req_folder_id = request.data.get('folder_id')
        req_task_id = request.data.get('task_id')
        req_hearing_id = request.data.get('hearing_id')
        req_notation_id = request.data.get('notation_id')
        req_contract_id = request.data.get('contract_id')
        if req_case_id not in (None, ''):
            comment = comments(id=None, case_id=req_case_id,
                               comment=request.data['comment'], created_by=request.user)
            comment.save()
            LitigationCases.objects.get(id=req_case_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        elif req_folder_id not in (None, ''):
            comment = comments(id=None, folder_id=req_folder_id, comment=request.data['comment'],
                               created_by=request.user)
            comment.save()
            Folder.objects.get(id=req_folder_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        elif req_task_id not in (None, ''):
            comment = comments(id=None, task_id=req_task_id,
                               comment=request.data['comment'], created_by=request.user)
            comment.save()
            task.objects.get(id=req_task_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        elif req_hearing_id not in (None, ''):
            comment = comments(id=None, hearing_id=req_hearing_id, comment=request.data['comment'],
                               created_by=request.user)
            comment.save()
            hearing.objects.get(id=req_hearing_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        elif req_notation_id not in (None, ''):
            comment = comments(id=None, notation_id=req_notation_id, comment=request.data['comment'],
                               created_by=request.user)
            comment.save()
            Notation.objects.get(id=req_notation_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        elif req_contract_id not in (None, ''):
            comment = comments(id=None, contract_id=req_contract_id, comment=request.data['comment'],
                               created_by=request.user)
            comment.save()
            Contract.objects.get(id=req_contract_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        else:
            return Response({'error_message': 'Please select one of Ids to add comment'},
                            status=status.HTTP_400_BAD_REQUEST)
        cache.delete("comments_queryset")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        comment = comments.objects.filter(id=pk)
        comment.update(is_deleted=True)
        comment.update(modified_by=request.user)
        comment.update(modified_at=timezone.now())
        cache.delete("comments_queryset")
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        cache.delete("comments_queryset")
        serializer.save(modified_by=self.request.user)

    def get_queryset(self):
        cache_key = "comments_queryset"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            queryset = cached_queryset
        else:
            queryset = comments.objects.all().order_by('-id').filter(is_deleted=False)
            cache.set(cache_key,queryset,timeout=None)
        return queryset

class repliesViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = replies.objects.all().order_by(
        '-created_at').filter(is_deleted=False)
    serializer_class = repliesSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    pagination_class = StandardResultsSetPagination
    perm_slug = "core.replies"

    def create(self, request):
        if "reply" in request.data:
            reply = replies(id=None, reply=request.data['reply'], comment_id=int(request.data['comment_id']),
                            created_by=request.user)
            reply.save()
            serializer = self.get_serializer(reply)
            if "comment_id" in request.data:
                comment_id = request.data['comment_id']
                comments.objects.get(id=comment_id).replies.add(reply)
                cache.delete("replies_queryset")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'no comment id'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'no reply'}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        reply = replies.objects.filter(id=pk)
        reply.update(is_deleted=True)
        reply.update(modified_by=request.user)
        reply.update(modified_at=timezone.now())
        cache.delete("replies_queryset")
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        cache.delete("replies_queryset")
        serializer.save(modified_by=self.request.user)

    def get_queryset(self):
        cache_key = "replies_queryset"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            queryset = cached_queryset
        else:
            queryset = replies.objects.all().order_by('-created_at').filter(is_deleted=False)
            cache.set(cache_key, queryset, timeout=None)
        return queryset

class prioritiesViewSet(viewsets.ModelViewSet):
    queryset = priorities.objects.all().order_by('priority')
    serializer_class = prioritiesSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.priorities"

class StatusViewSet(viewsets.ModelViewSet):
    queryset = Status.objects.all().order_by('status')
    serializer_class = StatusSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "core.Status"

class contractsViewSet(viewsets.ModelViewSet):
    queryset = contracts.objects.all().order_by(
        '-created_by').filter(is_deleted=False)
    serializer_class = contractsSerializer
    permission_classes = [permissions.IsAuthenticated, Manager_SuperUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        #   FullWordSearchFilter,
    ]
    perm_slug = "core.contracts"
    search_fields = ['@name', '=id']
    ordering_fields = ['created_at', 'id', 'modified_at']

    def create(self, request):
        req_name = request.data['name']
        req_attachement = request.FILES.get('attachment')
        contract = contracts(id=None, name=req_name,
                             attachment=req_attachement, created_by=request.user)
        contract.save()
        serializer = self.get_serializer(contract)
        cache.delete("contracts_queryset")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        contract = contracts.objects.filter(id=pk)
        contract.update(is_deleted=True)
        contract.update(modified_by=request.user)
        contract.update(modified_at=timezone.now())
        cache.delete("contracts_queryset")
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = contracts.objects.filter(
            is_deleted=False).order_by('-created_by')
        if request.user.is_manager == False or self.request.user.is_superuser == False:
            queryset = queryset.filter(created_by=request.user)
        contract = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(contract)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        cache_key = "contracts_queryset"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            queryset = cached_queryset
        else:
            queryset = contracts.objects.filter(is_deleted=False).order_by('-created_by')
            cache.set(cache_key, queryset, timeout=None)
        current_user = self.request.user
        if current_user.is_contract_manager or current_user.is_superuser or current_user.is_manager:
            queryset = queryset
        else:
            queryset.filter(created_by=current_user)

    def perform_update(self, serializer):
        cache.delete("contracts_queryset")
        serializer.save(modified_by=self.request.user)

class documentsViewSet(viewsets.ModelViewSet):
    queryset = documents.objects.all().order_by(
        '-created_by').filter(is_deleted=False)
    serializer_class = documentsSerializer
    permission_classes = [permissions.IsAuthenticated, Manager_SuperUser]
    perm_slug = "core.documents"
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        #   FullWordSearchFilter,
    ]
    filterset_fields = ['id', 'name', 'case_id', 'path_id']
    search_fields = ['@name', '=id']
    ordering_fields = ['created_at', 'id', 'modified_at']

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(documentsViewSet, self).dispatch(*args, **kwargs)

    def create(self, request):
        req_case_id = request.data.get(
            'case_id') if request.data.get('case_id') != '' else None
        req_path_id = request.data.get(
            'path_id') if request.data.get('path_id') != '' else None
        req_folder_id = request.data.get(
            'folder_id') if request.data.get('folder_id') != '' else None
        req_task_id = request.data.get(
            'task_id') if request.data.get('task_id') != '' else None
        req_hearing_id = request.data.get(
            'hearing_id') if request.data.get('hearing_id') != '' else None
        req_name = request.data.get('name')
        req_attachement = request.FILES.get('attachment')
        document = documents(id=None, name=req_name, case_id=req_case_id, path_id=req_path_id, folder_id=req_folder_id,
                             task_id=req_task_id, hearing_id=req_hearing_id, attachment=req_attachement,
                             created_by=request.user)
        document.save()
        if req_attachement in ('', None):
            return Response(data={"detail": "Please select Document to upload"}, status=status.HTTP_400_BAD_REQUEST)
        if req_case_id not in ('', None):
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            case.documents.add(document)
        if req_path_id not in ('', None):
            path = get_object_or_404(Path, pk=req_path_id)
            path.documents.add(document)
        if req_folder_id not in ('', None):
            path = get_object_or_404(Folder, pk=req_folder_id)
            path.documents.add(document)
        if req_task_id not in ('', None):
            Task = get_object_or_404(task, pk=req_task_id)
            Task.documents.add(document)
        if req_hearing_id not in ('', None):
            Hearing = get_object_or_404(hearing, pk=req_hearing_id)
            Hearing.documents.add(document)
        serializer = self.get_serializer(document)
        print(req_task_id)
        cache.delete("documents_queryset")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        docs = documents.objects.filter(id=pk)
        docs.update(is_deleted=True)
        docs.update(modified_by=request.user)
        docs.update(modified_at=timezone.now())
        case_msg, path_msg, folder_msg = '', '', ''
        doc = documents.objects.get(id=pk)
        if doc.case_id:
            case = get_object_or_404(LitigationCases, pk=doc.case_id)
            case.documents.remove(doc)
            case_msg = f' and deleted from Case #{doc.case_id}'
            doc.case_id = None
            doc.save()
        if doc.path_id:
            path = get_object_or_404(Path, pk=doc.path_id)
            path.documents.remove(doc)
            path_msg = f' and deleted from Path #{doc.path_id}'
            doc.path_id = None
            doc.save()
        if doc.folder_id:
            folder = get_object_or_404(Folder, pk=doc.folder_id)
            folder.documents.remove(doc)
            folder_msg = f' and deleted from Folder #{doc.folder_id}'
            doc.folder_id = None
            doc.save()
        for manager in User.objects.filter(is_manager=True):
            Notification.objects.create_notification(action='delete',
                                                     content_type=ContentType.objects.get_for_model(doc),
                                                     object_id=doc.id, object_name=doc.name, action_by=request.user,
                                                     user=manager,
                                                     role='manager')
        cache.delete("documents_queryset")
        return Response(data={"detail": f"Document is deleted {folder_msg}{path_msg}{case_msg}"},
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = documents.objects.filter(
            is_deleted=False).order_by('-created_by')
        if not request.user.is_manager and not request.user.is_superuser:
            queryset = queryset.filter(created_by=request.user)
        document = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(document)
        cache.delete("documents_queryset")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

    def get_queryset(self):
        cache_key = "documents_queryset"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            queryset = cached_queryset
        else:
            queryset = documents.objects.all().order_by('-created_by').filter(is_deleted=False)
            cache.set(cache_key, queryset, timeout=None)
        return queryset

class eventsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Events.objects.all().exclude(pgh_diff='')
    serializer_class = EventsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['pgh_obj_model', 'pgh_obj_id', ]

class caseseventsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Events.objects.all().exclude(pgh_diff='').filter(
        pgh_obj_model='cases.LitigationCases')
    serializer_class = EventsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['pgh_obj_model', 'pgh_obj_id', ]

    def destroy(self, request, pk=None):
        case = documents.objects.filter(id=pk)
        case.update(is_deleted=True)
        case.update(modified_by=request.user)
        case.update(modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

class APIDocumentPathListView(ExternalObjectAPIViewMixin, generics.ListAPIView):
    """
    Returns a list of all the Paths to which a document belongs.
    """
    external_object_queryset = documents.objects.all()
    external_object_pk_url_kwarg = 'document_id'

    def get_source_queryset(self):
        return self.get_external_object().Paths.all()

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(APIDocumentPathListView, self).dispatch(*args, **kwargs)

class APIPathListView(generics.ListCreateAPIView):
    """
    get: Returns a list of all the Paths.
    post: Create a new Path.
    """

    ordering_fields = ('id', 'name')
    pagination_class = StandardResultsSetPagination
    serializer_class = PathSerializer
    source_queryset = Path.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id', 'case_id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(APIPathListView, self).dispatch(*args, **kwargs)

    def create(self, request):
        req_name = request.data.get('name')
        req_parent = request.data.get('parent') if request.data.get('parent') not in ('', None) else None
        req_case_id = request.data.get('case_id') if request.data.get('case_id') not in ('', None) else None
        req_folder_id = request.data.get('folder_id') if request.data.get('folder_id') not in ('', None) else None
        req_admin_id = request.data.get('admin_id') if request.data.get('admin_id') not in ('', None) else None
        req_notation_id = request.data.get('notation_id') if request.data.get('notation_id') not in ('', None) else None
        req_contract_id = request.data.get('contract_id') if request.data.get('contract_id') not in ('', None) else None
        try:
            obj = Path.objects.get(parent=req_parent, name=req_name)
            return Response(data={"detail": f"اسم المجلد '{req_name}' موجود مسبقا"}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            if req_parent not in ('', None):
                req_parent = get_object_or_404(Path, pk=req_parent)
            path = Path(name=req_name, parent=req_parent,
                        case_id=req_case_id, folder_id=req_folder_id, notation_id=req_notation_id,
                        contract_id= req_contract_id, admin_id=req_admin_id, created_by=request.user,
                        created_at=timezone.now())
            path.save()
            if req_case_id:
                case = get_object_or_404(LitigationCases, pk=req_case_id)
                case.paths.add(path)
            if req_folder_id:
                folder = get_object_or_404(Folder, pk=req_folder_id)
                folder.paths.add(path)
            if req_admin_id:
                admin = get_object_or_404(AdministrativeInvestigation, pk=req_admin_id)
                admin.paths.add(path)
            if req_notation_id:
                notation = get_object_or_404(Notation, pk=req_notation_id)
                notation.paths.add(path)
            if req_contract_id:
                contract = get_object_or_404(Contract, pk=req_contract_id)
                contract.paths.add(path)
            serializer = self.get_serializer(path)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        parent = serializer.validated_data['parent']
        if parent:
            queryset = self.get_source_queryset()
            get_object_or_404(Path, pk=parent.pk)

        return super().perform_create(serializer)

## APIPathView OLD START

## The old APIPathView Start ##
# class APIPathView(rest_framework_generics.RetrieveUpdateDestroyAPIView):
#
#     lookup_url_kwarg = 'path_id'
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = PathSerializer
#     queryset = Path.objects.all()
#     pagination_class = StandardResultsSetPagination
#     filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
#     filterset_fields = ['case_id']
#     ordering_fields = ['created_at', 'id', 'modified_at']
#     ordering = ['-id']
#     authentication_classes = [TokenAuthentication, SessionAuthentication]
#
#     def get_instance_extra_data(self):
#         return {
#             '_event_actor': self.request.user
#         }
#
#     def destroy(self, request, *args, **kwargs):
#         path_id = kwargs['path_id']
#         path = Path.objects.filter(id=path_id)
#         paths = Path.objects.get(id=path_id)
#         case_msg, folder_msg = '', ''
#         paths.documents.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now(),
#                                      path_id=None)
#         path.delete()
#         for manager in User.objects.filter(is_manager=True):
#             Notification.objects.create_notification(action='delete',
#                                                      content_type=ContentType.objects.get_for_model(paths),
#                                                      object_id=paths.id, object_name=paths.name, action_by=request.user,
#                                                      user=manager,
#                                                      role='manager')
#         return Response(data={"detail": f"Path is deleted{case_msg}{folder_msg}"}, status=status.HTTP_200_OK)
#
#     def perform_update(self, serializer):
#         serializer.save(modified_by=self.request.user)
#
#     def get_object(self):
#         parent_id = self.kwargs['path_id']  # Assuming the URL parameter is named 'pk'
#         parent_node = Path.objects.get(id=parent_id)  # Replace with your actual model
#
#         current_user = self.request.user
#         children = parent_node.get_children()
#         if current_user.is_manager or current_user.is_superuser:
#             children = parent_node.get_children()
#         elif current_user.is_contract_manager and parent_id == '24':
#             children = parent_node.get_children()
#         else:
#             filter_query = Q(assignee__exact=current_user) | Q(
#                 created_by__exact=current_user) | Q(shared_with__exact=current_user)
#             cases = LitigationCases.objects.filter(filter_query).distinct()
#             admins = AdministrativeInvestigation.objects.filter(filter_query).distinct()
#             notations = Notation.objects.filter(filter_query).distinct()
#             contracts = Contract.objects.filter(filter_query).distinct()
#             folders = Folder.objects.filter(filter_query).distinct()
#             cases_ids = cases.values_list('id', flat=True)
#             admins_ids = admins.values_list('id', flat=True)
#             notations_ids = notations.values_list('id', flat=True)
#             contract_ids = contracts.values_list('id', flat=True)
#             folders_ids = folders.values_list('id', flat=True)
#             child_filter_query = (Q(created_by__exact=current_user) | Q(case_id__in=cases_ids) | Q(
#                 admin_id__in=admins_ids) | Q(notation_id__in=notations_ids) | Q(folder_id__in=folders_ids) |
#                                   Q(contract_id__in=contract_ids))
#             children = parent_node.get_children().filter(child_filter_query).distinct()
#         current_user = self.request.user
#         parent_node.filtered_children = children
#         parent_node.current_user = current_user
#         return parent_node

## The old APIPathView End ##

## APIPathView OLD END

class APIPathView_old(rest_framework_generics.RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = 'path_id'
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PathSerializer
    queryset = Path.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['case_id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user
        }

    def destroy(self, request, *args, **kwargs):
        path_id = kwargs['path_id']
        path = Path.objects.filter(id=path_id)
        paths = Path.objects.get(id=path_id)
        case_msg, folder_msg = '', ''
        paths.documents.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now(),
                                     path_id=None)
        path.delete()
        for manager in User.objects.filter(is_manager=True):
            Notification.objects.create_notification(action='delete',
                                                     content_type=ContentType.objects.get_for_model(paths),
                                                     object_id=paths.id, object_name=paths.name, action_by=request.user,
                                                     user=manager,
                                                     role='manager')
        cache.delete(f"path_{path}_queryset")
        return Response(data={"detail": f"Path is deleted{case_msg}{folder_msg}"}, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)


    def get_object(self):
        # Retrieve the parent node dynamically based on the ID in the URL
        parent_id = self.kwargs['path_id']  # Assuming the URL parameter is named 'pk'
        cache_key = f"path_{parent_id}_queryset"
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            parent_node = cached_queryset
        else:
            parent_node = Path.objects.get(id=parent_id)
            cache.set(cache_key, parent_node, timeout=None)
        # Filter the children nodes of the parent node created by the current user
        current_user = self.request.user
        children = parent_node.get_children()
        if current_user.is_manager or current_user.is_superuser:
            children = parent_node.get_children()
        elif current_user.is_contract_manager and parent_id == '24':
            children = parent_node.get_children()
        else:
            filter_query = Q(assignee__exact=current_user) | Q(
                created_by__exact=current_user) | Q(shared_with__exact=current_user)
            cases_cache_key = f"case_{filter_query}"
            cases_cached_queryset = cache.get(cases_cache_key)
            if cases_cached_queryset:
                cases = cases_cached_queryset
            else:
                cases = LitigationCases.objects.filter(filter_query).distinct()
                cache.set(cache_key, cases, timeout=None)

            admins_cache_key = f"admins_{filter_query}"
            admins_cached_queryset = cache.get(admins_cache_key)
            if admins_cache_key:
                admins = admins_cache_key
            else:
                admins = AdministrativeInvestigation.objects.filter(filter_query).distinct()
                cache.set(admins_cache_key, admins, timeout=None)
            notations = Notation.objects.filter(filter_query).distinct()
            folders = Folder.objects.filter(filter_query).distinct()
            cases_ids = cases.values_list('id', flat=True)
            admins_ids = admins.values_list('id', flat=True)
            notations_ids = notations.values_list('id', flat=True)
            folders_ids = folders.values_list('id', flat=True)
            child_filter_query = Q(created_by__exact=current_user) | Q(case_id__in=cases_ids) | Q(
                admin_id__in=admins_ids) | Q(notation_id__in=notations_ids) | Q(folder_id__in=folders_ids)
            # queryset = queryset.filter(filter_query).distinct()
            children = parent_node.get_children().filter(child_filter_query).distinct()
        # parent_node.children.set(children)
        current_user = self.request.user
        parent_node.filtered_children = children
        parent_node.current_user = current_user
        # Include both the parent object and its children in the response
        return parent_node

class APIPathView(rest_framework_generics.RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = 'path_id'
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PathSerializer
    queryset = Path.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['case_id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_object(self):
        """Retrieve the cached parent node dynamically."""
        path_id = self.kwargs["path_id"]
        cache_key = f"path_{path_id}_queryset"
        parent_node = cache.get(cache_key)

        if parent_node is None:
            parent_node = Path.objects.select_related("parent").get(id=path_id)
            cache.set(cache_key, parent_node, timeout=None)

        current_user = self.request.user
        children_cache_key = f"path_{path_id}_children_{current_user.id}"
        cached_children = cache.get(children_cache_key)

        if cached_children is None:
            children_query = parent_node.get_children()

            if not current_user.is_superuser and not current_user.is_manager:
                filter_query = Q(created_by=current_user) | Q(shared_with=current_user) | Q(assignee=current_user)
                cases = LitigationCases.objects.filter(filter_query).values_list("id", flat=True)
                child_filter_query = Q(created_by=current_user) | Q(case_id__in=cases)
                children_query = children_query.filter(child_filter_query).distinct()

            cached_children = children_query
            cache.set(children_cache_key, cached_children, timeout=None)

        parent_node.filtered_children = cached_children
        return parent_node

    def destroy(self, request, *args, **kwargs):
        """Delete a path and update the cache."""
        path_id = kwargs["path_id"]
        path = Path.objects.filter(id=path_id).first()

        if not path:
            return Response({"detail": "Path not found."}, status=status.HTTP_404_NOT_FOUND)

        path.documents.update(
            is_deleted=True, modified_by=request.user, modified_at=timezone.now(), path_id=None
        )
        path.delete()

        # Send notifications to managers
        for manager in User.objects.filter(is_manager=True):
            Notification.objects.create_notification(
                action="delete",
                content_type=ContentType.objects.get_for_model(Path),
                object_id=path_id,
                object_name=path.name,
                action_by=request.user,
                user=manager,
                role="manager",
            )

        # Delete cache entries
        cache.delete(f"path_{path_id}_queryset")
        cache.delete(f"path_{path_id}_children_{request.user.id}")

        return Response({"detail": "Path deleted successfully."}, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

class APIPathDocumentAddView(generics.ObjectActionAPIView):
    """
    post: Add a document to a Path.
    """
    lookup_url_kwarg = 'path_id'

    serializer_class = PathDocumentAddSerializer
    source_queryset = Path.objects.all()

    def object_action(self, obj, request, serializer):
        document = serializer.validated_data['document']
        obj.document_add(document=document, user=self.request.user)

class APIPathDocumentRemoveView(generics.ObjectActionAPIView):
    """
    post: Remove a document from a Path.
    """
    lookup_url_kwarg = 'path_id'

    serializer_class = PathDocumentRemoveSerializer
    source_queryset = Path.objects.all()

    def object_action(self, obj, request, serializer):
        document = serializer.validated_data['document']
        obj.document_remove(document=document, user=self.request.user)

class APIPathDocumentListView(ExternalObjectAPIViewMixin, generics.ListAPIView):
    """
    get: Returns a list of all the documents contained in a particular Path.
    """
    pagination_class = StandardResultsSetPagination
    external_object_class = Path
    external_object_pk_url_kwarg = 'path_id'
    serializer_class = documentsSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_source_queryset(self):
        return documents.objects.filter(
            pk__in=self.get_external_object().documents.only('pk')
        )

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        Manager_SuperUser
    ]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Notification.objects.all().order_by('-action_at').filter(is_deleted=False)
    serializer_class = NotificationSerializer
    pagination_class = LimitOffsetPagination
    ordering_fields = ['action_at', 'id', ]

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(60 * 60))
    # def dispatch(self, *args, **kwargs):
    #     return super(NotificationViewSet, self).dispatch(*args, **kwargs)

    @action(methods=['post'], detail=True, serializer_class=None)
    def read(self, request, pk):
        notification = self.get_object()
        notification.is_read = True
        notification.browser_read = True
        notification.save()
        return Response(status=status.HTTP_200_OK, data={'details': 'done'})

    @action(methods=['post'], detail=True, serializer_class=None)
    def browser_read(self, request, pk):
        notification = self.get_object()
        notification.browser_read = True
        notification.save()
        return Response(status=status.HTTP_200_OK, data={'details': 'done'})

    @action(methods=['post'], detail=True, serializer_class=None)
    def unread(self, request, pk):
        notification = self.get_object()
        notification.is_read = False
        notification.save()
        return Response(status=status.HTTP_200_OK, data={'details': 'done'})

    @action(methods=['post'], detail=True, serializer_class=None)
    def delete(self, request, pk):
        notification = self.get_object()
        notification.is_deleted = True
        notification.save()
        return Response(status=status.HTTP_200_OK, data={'details': 'done'})

    @action(methods=['post'], detail=False, serializer_class=None)
    def read_all(self, request):
        Notification.objects.filter(
            is_deleted=False, user=request.user).update(is_read=True, browser_read=True)
        return Response(status=status.HTTP_200_OK, data={'details': 'done'})

    @action(methods=['post'], detail=False, serializer_class=None)
    def unread_all(self, request):
        Notification.objects.filter(
            is_deleted=False, is_read=True).update(is_read=False)
        return Response(status=status.HTTP_200_OK, data={'details': 'done'})

    @action(methods=['post'], detail=False, serializer_class=None)
    def delete_all(self, request):
        notifications = Notification.objects.filter(
            is_deleted=False, user=request.user).update(is_deleted=True)
        return Response(status=status.HTTP_200_OK, data={'details': 'done'})

    def get_queryset(self):
        current_user_id = self.request.user.id
        # cuser = User.objects.get(id=current_user_id)
        # is_manager = cuser.is_manager
        # is_superuser = cuser.is_superuser
        queryset = Notification.objects.filter(
            is_deleted=False, user=current_user_id).order_by('-action_at')
        # if is_manager or is_superuser:
        #     queryset = queryset
        # else:
        #     queryset = []
        return queryset

    # def list(self, request):
    #     unread_count = self.get_queryset().filter(is_read=False).count()
    #     qs = self.get_queryset()
    #     serializer = self.get_serializer(qs,many=True)
    #     count = self.get_queryset().count()
    #     paginator = LimitOffsetPagination()
    #     paginator_response = paginator.paginate_queryset(serializer.data,request)
    #     # count = paginator_response.get_count
    #     print('count',count)
    #     response_data = OrderedDict([
    #             # ('count', count),
    #             ('results', paginator_response),
    #             ('unread_count', unread_count),
    #         ])
    #     return self.get_paginated_response(serializer.data)
    #     # return Response(response_data, status=status.HTTP_200_OK)

    def alter_response_data(self, _json_response):
        json_response = _json_response.copy()
        results = []
        next_ = json_response['next']
        previous_ = json_response['previous']
        unread_count = self.get_queryset().filter(is_read=False).count()
        json_response['unseen_count'] = unread_count
        for item in json_response['results']:
            item.update({'next': next_, 'previous': previous_})
            results.append(item)
        json_response['results'] = results
        return json_response

    def dispatch(self, request, *args, **kwargs):
        http_response = super().dispatch(request, *args, **kwargs)
        json_response = http_response.data

        if 'next' in json_response and 'previous' in json_response:
            http_response.data = self.alter_response_data(json_response)

        return http_response

# def get_nested_children(path):
#     children = Path.objects.filter(parent=path)
#     serialized_children = []
#     for child in children:
#         child_data = YourMPTTModelSerializer(child).data
#         child_data['children'] = get_nested_children(child)
#         serialized_children.append(child_data)
#     return serialized_children
#
#
# from rest_framework.decorators import api_view
#
# @api_view(['GET'])
# def selected_path_children(request, pk):
#     selected_path = get_object_or_404(Path, pk=pk)
#     serialized_tree = YourMPTTModelSerializer(selected_path).data
#     serialized_tree['children'] = get_nested_children(selected_path)
#     return Response(serialized_tree, status=status.HTTP_200_OK)


class IsSuperOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_superuser and not request.user.is_manager

class IsContractManager(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is a contract manager
        return request.user.is_contract_manager

class HasRelatedModelPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if isinstance(obj, LitigationCases):
            # Check if the user is in 'assignee', 'created_by', or 'shared_with' fields
            return (
                user in obj.assignee.all() or
                user == obj.created_by or
                user in obj.shared_with.all()
            )
        elif isinstance(obj, AdministrativeInvestigation):
            # Check if the user is in 'assignee', 'created_by', or 'shared_with' fields
            return (
                user in obj.assignee.all() or
                user == obj.created_by or
                user in obj.shared_with.all()
            )
        elif isinstance(obj, Notation):
            # Check if the user is in 'assignee', 'created_by', or 'shared_with' fields
            return (
                user in obj.assignee.all() or
                user == obj.created_by or
                user in obj.shared_with.all()
            )
        elif isinstance(obj, Folder):
            # Check if the user is in 'assignee', 'created_by', or 'shared_with' fields
            return (
                user in obj.assignee.all() or
                user == obj.created_by or
                user in obj.shared_with.all()
            )
        return False  # Return False for other objects

class SelectedPathChildren(generics.RetrieveAPIView):
    serializer_class = YourMPTTModelSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [HasRelatedModelPermission,]
    pagination_class = StandardResultsSetPagination


    def get_source_queryset(self):
        return Path.objects.all()

    def retrieve(self, request, pk=None):
        selected_path = Path.objects.get(pk=pk)  # Retrieve the selected Path

        # Extract the 'limit' and 'skip' query parameters
        limit = int(request.query_params.get('limit', 10))  # Default to 10 if not specified
        skip = int(request.query_params.get('skip', 0))  # Default to 0 if not specified


        def get_nested_children(path):
            path_id = None
            if isinstance(path, dict):
                path_id = path['id']
            else:
                path_id = path.id
            children = Path.objects.filter(parent=path_id)
            children = children[skip:skip + limit]
            serialized_children = YourMPTTModelSerializer(children, many=True).data
            for child in serialized_children:
                child['subPaths'] = get_nested_children(child)
            return serialized_children

        serialized_tree = YourMPTTModelSerializer(selected_path).data
        serialized_tree['subPaths'] = get_nested_children(selected_path)

        return Response(serialized_tree)


@login_required
def Paths_list(request):
    number_of_records = 10
    keywords = priority = None
    user = request.user
    if request.method == 'GET':
        # Clear filters and redirect if needed.
        if request.GET.get('clear'):
            for key in ['keywords', 'number_of_records']:
                request.session.pop(key, None)
            return redirect(request.path)

        # Retrieve filter parameters from GET or session.
        if 'keywords' in request.GET:
            keywords = request.GET.get('keywords')
            request.session['keywords'] = keywords  # Update session even if empty
        else:
            keywords = request.session.get('keywords', '')

        # Save parameters to session if provided.
        for key, value in (('keywords', keywords),):
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

        # Get base queryset.
        cache_key = "Paths_objects"
        cached_data = cache.get(cache_key)
        if cached_data:
            Paths_qs = cached_data
        else:
            Paths_qs = Path.objects.filter(is_deleted=False).exclude(id=24).exclude(parent=24).order_by(
                '-created_by')
            cache.set(cache_key, Paths_qs, timeout=None)
        Paths_qs = Paths_qs.filter(query)
        # Retrieve filter dropdown data from cache or compute if not cached.
        if user.is_manager or user.is_superuser:
            Paths_qs = Paths_qs
        elif user.is_cases_public_manager:
            # Apply filters.
            Paths_qs = Paths_qs

        else:
            cases_filter = Q(cases__shared_with=user) | Q(cases__created_by=user) | Q(cases__assignee=user)
            admins_filter = Q(AdministrativeInvestigations__shared_with=user) | Q(AdministrativeInvestigations__created_by=user) | Q(AdministrativeInvestigations__assignee=user)
            notations_filter = Q(notations__shared_with=user) | Q(notations__created_by=user) | Q(notations__assignee=user)
            folders_filter = Q(folders__shared_with=user) | Q(folders__created_by=user) | Q(folders__assignee=user)
            contracts_filter = Q(contracts__shared_with=user) | Q(contracts__created_by=user) | Q(contracts__assignee=user)
            filter_query= Q()
            filter_query.add(cases_filter,Q.OR)
            filter_query.add(notations_filter,Q.OR)
            filter_query.add(admins_filter,Q.OR)
            filter_query.add(folders_filter,Q.OR)
            filter_query.add(contracts_filter,Q.OR)
            Paths_qs = Paths_qs.filter(filter_query)
    else:
        Paths_qs = Path.objects.filter(is_deleted=False).order_by(
            '-created_by')

    # Set up pagination.
    paginator = Paginator(Paths_qs, number_of_records)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=2, on_ends=2)

    # Prepare session info for the template.
    session_info = {
        'number_of_records': number_of_records or 10,
        'keywords': keywords or '',
    }

    # Build a filter query string to be used in pagination links.
    # Only include filter keys (exclude 'page').
    filter_params = {}
    for key in ['keywords', 'number_of_records']:
        value = request.session.get(key)
        if value:
            filter_params[key] = value
    filter_query = urlencode(filter_params)
    objs_count = Paths_qs.count()
    fields_to_show = [
        'id', 'name', 'created_at',
    ]

    headers = [
        _("Number"), _("Name"), _("Created At"), _("Actions")
    ]
    filter_fields = [
        {
            "name": "keywords",
            "label": _("Search keywords"),
            "type": "text",
            "value": keywords,
        },
    ]
    context = {
        'fields_to_show': fields_to_show,
        'headers': headers,
        'new_path':'hearing_create',
        'objs': page_obj,
        'objs_count': objs_count,
        'page_range': page_range,
        'session': json.dumps(session_info),
        'filter_fields': filter_fields,
        'filter_query': filter_query,  # New variable for pagination links.
    }
    return render(request, 'paths_list.html', context)


@require_POST
def new_path_docs(request, path_id=None):
    instance = get_object_or_404(Path, pk=path_id)
    print(f'{request.FILES.items()=}')
    print(f'{request.POST=}')
    files = request.FILES.getlist('attachments')
    url = request.POST.get('url')
    for uploaded_file in files:
        print(f'{uploaded_file=}')
        doc = documents.objects.create(
            name=uploaded_file.name,
            attachment=uploaded_file,
            created_by=request.user,
            created_at=timezone.now(),
        )
        instance.documents.add(doc)
    return redirect(url)

@require_POST
def delete_path(request, path_id=None):
    instance = get_object_or_404(Path, pk=path_id)
    instance.is_deleted = True
    instance.modified_by = request.user
    instance.modified_at = timezone.now()
    instance.save()
    return JsonResponse({'success': True, 'message': _('Path has been deleted successfully.')}, status=200)

@require_POST
def delete_document(request, doc_id=None):
    instance = get_object_or_404(documents, pk=doc_id)
    instance.is_deleted = True
    instance.modified_by = request.user
    instance.modified_at = timezone.now()
    instance.save()
    return JsonResponse({'success': True, 'message': _('Document has been deleted successfully.')}, status=200)

@require_POST
def new_case_comment_reply(request, case_id=None, comment_id=None):
    instance = get_object_or_404(comments, pk=comment_id)
    instance.replies.create(reply=request.POST.get('content'),created_by=request.user,created_at=timezone.now())
    return redirect('case_view',case_id=case_id)

@require_POST
def new_comment_reply(request, comment_id=None):
    url = request.POST.get('url')
    instance = get_object_or_404(comments, pk=comment_id)
    instance.replies.create(reply=request.POST.get('content'),created_by=request.user,created_at=timezone.now())
    return redirect(url)