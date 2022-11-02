from accounts.models import User
from django.contrib.auth.models import Group
from rest_framework import serializers
from cases.models import Group
from core.models import comments,replies
from drf_dynamic_fields import DynamicFieldsMixin

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class repliesSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = replies
        fields = ['id', 'reply','comment_id','created_by','created_at','modified_by','modified_at']

class commentsSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    replies = repliesSerializer(many=True)
    class Meta:
        ref_name = 'Comments'
        model = comments
        fields = ['id', 'comment','replies','case_id','event_id','task_id','hearing_id','created_by','created_at','modified_by','modified_at']
