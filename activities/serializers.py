from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from .models import task,event,hearing_type,hearing,task_type,event_type


class task_typeSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = task_type
        fields = ['id', 'type']

class event_typeSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = event_type
        fields = ['id', 'type']

class hearing_typeSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = hearing_type
        fields = ['id', 'type']

class taskSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    task_type = task_typeSerializer()
    class Meta:
        model = task
        fields = ['id', 'name','task_type','description','assigned_to','requested_by','priority','due_date','comments']

class eventSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    event_type = event_typeSerializer()
    class Meta:
        model = event
        fields = ['id', 'event_type','created_by','from_date','to_date','attendees','comments']

class hearingSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = hearing
        fields = ['id', 'name','hearing_type','hearing_date','assignee','time_spent','comments','summary_by_lawyer','attachment']

