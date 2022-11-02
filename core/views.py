from audioop import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from rest_framework import viewsets,status
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import comments,replies
from .serializers import GroupSerializer, commentsSerializer,  repliesSerializer
from cases.models import LitigationCases
from activities.models import event,task,hearing
from django.views.decorators.cache import cache_page
from django.core.cache import cache

# def com_all():
#     comments = cache.get('comments')
#     if comments is None:
#         comments = comments.objects.all().order_by('-created_at')
#         cache.set('comments', comments)
#     return comments

@cache_page(60 * 15)
def home(request):
    context = {}
    return render(request, 'index.html', context=context)

@cache_page(60 * 15)
def about(request):
    return render(request, 'about.html')


class GroupViewSet(viewsets.ModelViewSet):

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class commentsViewSet(viewsets.ModelViewSet):

    queryset = comments.objects.all().order_by('-created_at')
    serializer_class = commentsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        if "comment" in request.data:
            comment = comments(id=None,comment=request.data['comment'],created_by=request.user)
            comment.save()
            serializer = self.get_serializer(comment)
            if "case_id" in request.data:
                case_id = request.data['case_id']
                LitigationCases.objects.get(id=case_id).comments.add(comment)
            if "event_id" in request.data:
                event_id = request.data['event_id']
                event.objects.get(id=event_id).comments.add(comment)
            if "task_id" in request.data:
                task_id = request.data['task_id']
                task.objects.get(id=task_id).comments.add(comment)
            if "hearing_id" in request.data:
                hearing_id = request.data['hearing_id']
                hearing.objects.get(id=hearing_id).comments.add(comment)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            return Response({'error':'no comment'},status=status.HTTP_201_CREATED)

class repliesViewSet(viewsets.ModelViewSet):

    queryset = replies.objects.all().order_by('-created_at')
    serializer_class = repliesSerializer
    permission_classes = [permissions.IsAuthenticated]

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
                return Response({'error':'no reply'},status=status.HTTP_201_CREATED)
