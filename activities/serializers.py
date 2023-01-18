from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from .models import task,hearing
from core.models import court,Status
from accounts.models import User
from cases.models import LitigationCases


# class task_typeSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
#     class Meta:
#         model = task_type
#         fields = ['id', 'type']

# class event_typeSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
#     class Meta:
#         model = event_type
#         fields = ['id', 'type']

# class hearing_typeSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
#     class Meta:
#         model = hearing_type
#         fields = ['id', 'type']

class taskSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    assignee = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    task_status = serializers.SlugRelatedField(slug_field='status',queryset=Status.objects.all())
    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    class Meta:
        model = task
        fields = ['id', 'title','description','assignee','due_date','comments','case_id','task_status','created_by','created_at','modified_by','modified_at']
        extra_kwargs = {'created_by': {'required': False},'modified_by': {'required': False}}
# class eventSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
#     event_type = event_typeSerializer()
#     class Meta:
#         model = event
#         fields = ['id', 'event_type','created_by','from_date','to_date','attendees','comments']


class hearingSerializer(DynamicFieldsMixin,serializers.ModelSerializer):

    name = serializers.CharField(max_length=200,required=False, allow_null=True)
    hearing_date = serializers.DateTimeField(required=False, allow_null=True)
    assignee = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    court = serializers.SlugRelatedField(slug_field='name',queryset=court.objects.all())
    hearing_status = serializers.SlugRelatedField(slug_field='status',queryset=Status.objects.all())
    comments_by_lawyer = serializers.CharField(max_length=200,required=False, allow_null=True)
    case_id = serializers.IntegerField(required=False, allow_null=True)
    case_name = serializers.SerializerMethodField('get_case_name')
    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    def get_case_name(self, obj):
        if obj.case_id:
            try:
                case =  LitigationCases.objects.get(id=obj.case_id).name
            except LitigationCases.DoesNotExist:
                case = None
            return case
        else:
            return None

    class Meta:
        model = hearing
        fields = ['id', 'name','hearing_date','assignee','court','comments_by_lawyer','case_id','hearing_status','case_name','created_by','created_at','modified_by','modified_at']
        extra_kwargs = {'created_by': {'required': False},'modified_by': {'required': False}}
