from django.contrib.auth.models import Group
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.response import Response

from activities.models import task, hearing
from cases.models import LitigationCases, Folder
from core.models import comments, replies, priorities, contracts, documents, Status, Path
from .serializers import EventsSerializer, GroupSerializer, commentsSerializer, repliesSerializer, prioritiesSerializer, \
    contractsSerializer, documentsSerializer, StatusSerializer
from datetime import datetime, timedelta
from cases.utils import Calendar
from django.utils.safestring import mark_safe
import calendar
from datetime import date
from .permissions import MyPermission
import django_filters.rest_framework
from django.utils import timezone
from pghistory.models import Events
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import (
    PathDocumentAddSerializer, PathDocumentRemoveSerializer,
    PathSerializer
)

from django.core.exceptions import ObjectDoesNotExist
from rest_api.api_view_mixins import ExternalObjectAPIViewMixin
from rest_api import generics
from rest_framework import generics as rest_framework_generics
from core.classes import StandardResultsSetPagination


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
        'cases': cases,
        'calendar': mark_safe(html_cal),
        'prev_month': pre_month,
        'next_month': nex_month
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
    pagination_class = StandardResultsSetPagination
    perm_slug = "core.comments"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id', 'case_id', 'task_id', 'hearing_id']

    def create(self, request):
        comment = []
        serializer = []
        if "case_id" in request.data:
            req_case_id = request.data['case_id']
            comment = comments(id=None, case_id=req_case_id, comment=request.data['comment'], created_by=request.user)
            comment.save()
            LitigationCases.objects.get(id=req_case_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        if "folder_id" in request.data:
            req_folder_id = request.data['folder_id']
            comment = comments(id=None, folder_id=req_folder_id, comment=request.data['comment'],
                               created_by=request.user)
            comment.save()
            Folder.objects.get(id=req_folder_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        if "task_id" in request.data:
            req_task_id = request.data['task_id']
            comment = comments(id=None, task_id=req_task_id, comment=request.data['comment'], created_by=request.user)
            comment.save()
            task.objects.get(id=req_task_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        if "hearing_id" in request.data:
            req_hearing_id = request.data['hearing_id']
            comment = comments(id=None, hearing_id=req_hearing_id, comment=request.data['comment'],
                               created_by=request.user)
            comment.save()
            hearing.objects.get(id=req_hearing_id).comments.add(comment)
            serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        comment = comments.objects.filter(id=pk)
        comment.update(is_deleted=True)
        comment.update(modified_by=request.user)
        comment.update(modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)


class repliesViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    queryset = replies.objects.all().order_by('-created_at').filter(is_deleted=False)
    serializer_class = repliesSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
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
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)


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
    queryset = contracts.objects.all().order_by('-created_by').filter(is_deleted=False)
    serializer_class = contractsSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
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
        contract = contracts(id=None, name=req_name, attachment=req_attachement, created_by=request.user)
        contract.save()
        serializer = self.get_serializer(contract)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        contract = contracts.objects.filter(id=pk)
        contract.update(is_deleted=True)
        contract.update(modified_by=request.user)
        contract.update(modified_at=timezone.now())
        return Response(data={"detail": "Record is deleted"}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = contracts.objects.filter(is_deleted=False).order_by('-created_by')
        if request.user.is_manager == False:
            queryset = queryset.filter(created_by=request.user)
        contract = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(contract)
        return Response(serializer.data, status=status.HTTP_200_OK)


class documentsViewSet(viewsets.ModelViewSet):
    queryset = documents.objects.all().order_by('-created_by').filter(is_deleted=False)
    serializer_class = documentsSerializer
    permission_classes = [permissions.IsAuthenticated, MyPermission]
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

    def create(self, request):
        req_case_id = request.data.get('case_id') if request.data.get('case_id') != '' else None
        req_path_id = request.data.get('path_id') if request.data.get('path_id') != '' else None
        req_folder_id = request.data.get('folder_id') if request.data.get('folder_id') != '' else None
        req_name = request.data.get('name')
        req_attachement = request.FILES.get('attachment')
        document = documents(id=None, name=req_name, case_id=req_case_id, path_id=req_path_id, folder_id=req_folder_id,
                             attachment=req_attachement, created_by=request.user)
        document.save()
        if req_attachement in ('', None):
            return Response(data={"detail": "Please select Document to upload"}, status=status.HTTP_400_BAD_REQUEST)
        if not req_case_id in ('', None):
            case = get_object_or_404(LitigationCases, pk=req_case_id)
            case.documents.add(document)
        if not req_path_id in ('', None):
            path = get_object_or_404(Path, pk=req_path_id)
            path.documents.add(document)
        if not req_folder_id in ('', None):
            path = get_object_or_404(Folder, pk=req_folder_id)
            path.documents.add(document)
        serializer = self.get_serializer(document)
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
        return Response(data={"detail": f"Document is deleted {folder_msg}{path_msg}{case_msg}"},
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = documents.objects.filter(is_deleted=False).order_by('-created_by')
        if request.user.is_manager == False:
            queryset = queryset.filter(created_by=request.user)
        document = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)


class eventsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Events.objects.all().exclude(pgh_diff='')
    serializer_class = EventsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['pgh_obj_model', 'pgh_obj_id', ]


class caseseventsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Events.objects.all().exclude(pgh_diff='').filter(pgh_obj_model='cases.LitigationCases')
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


class APIDocumentPathListView(
    ExternalObjectAPIViewMixin, generics.ListAPIView
):
    """
    Returns a list of all the Paths to which a document belongs.
    """
    external_object_queryset = documents.objects.all()
    external_object_pk_url_kwarg = 'document_id'

    def get_source_queryset(self):
        return self.get_external_object().Paths.all()


class APIPathListView(generics.ListCreateAPIView):
    """
    get: Returns a list of all the Paths.
    post: Create a new Path.
    """

    ordering_fields = ('id', 'name')
    serializer_class = PathSerializer
    source_queryset = Path.objects.all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['id', 'case_id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    def create(self, request):
        req_name = request.data.get('name')
        req_parent = request.data.get('parent')
        req_case_id = request.data.get('case_id') if request.data.get('case_id') != '' else None
        req_folder_id = request.data.get('folder_id') if request.data.get('folder_id') != '' else None

        try:
            obj = Path.objects.get(parent=req_parent, name=req_name)
            return Response(data={"detail": f"اسم المجلد '{req_name}' موجود مسبقا"}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            if not req_parent in ('', None):
                req_parent = get_object_or_404(Path, pk=req_parent)
            path = Path(name=req_name, parent=req_parent, case_id=req_case_id, folder_id=req_folder_id)
            path.save()
            if not req_case_id in ('', None):
                case = get_object_or_404(LitigationCases, pk=req_case_id)
                case.paths.add(path)
            if not req_folder_id in ('', None):
                folder = get_object_or_404(Folder, pk=req_folder_id)
                folder.paths.add(path)
            serializer = self.get_serializer(path)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        parent = serializer.validated_data['parent']
        if parent:
            queryset = self.get_source_queryset()
            get_object_or_404(Path, pk=parent.pk)

        return super().perform_create(serializer)


class APIPathView(rest_framework_generics.RetrieveUpdateDestroyAPIView):
    """
    delete: Delete the selected Path.
    get: Returns the details of the selected Path.
    patch: Edit the selected Path.
    put: Edit the selected Path.
    """
    lookup_url_kwarg = 'path_id'

    serializer_class = PathSerializer
    queryset = Path.objects.all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['case_id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user
        }

    def destroy(self, request, *args, **kwargs):
        path_id = kwargs['path_id']
        path = Path.objects.filter(id=path_id)
        paths = Path.objects.get(id=path_id)
        case_msg, folder_msg = '', ''
        if paths.case_id:
            case = get_object_or_404(LitigationCases, pk=paths.case_id)
            case.paths.remove(paths)
            case_msg = f' and deleted from Case #{paths.case_id}'
            paths.case_id = None
            paths.save()
        if paths.folder_id:
            folder = get_object_or_404(Folder, pk=paths.folder_id)
            folder.paths.remove(paths)
            folder_msg = f' and deleted from Folder #{paths.folder_id}'
            paths.folder_id = None
            paths.save()
        paths.documents.all().update(is_deleted=True, modified_by=request.user, modified_at=timezone.now(),
                                     path_id=None)
        path.delete()
        return Response(data={"detail": f"Path is deleted{case_msg}{folder_msg}"}, status=status.HTTP_200_OK)


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


class APIPathDocumentListView(
    ExternalObjectAPIViewMixin, generics.ListAPIView
):
    """
    get: Returns a list of all the documents contained in a particular Path.
    """
    external_object_class = Path
    external_object_pk_url_kwarg = 'path_id'
    serializer_class = documentsSerializer

    def get_source_queryset(self):
        return documents.objects.filter(
            pk__in=self.get_external_object().documents.only('pk')
        )
