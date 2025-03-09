from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from accounts.models import User
from cases.models import LitigationCases, Folder
from core.models import court, Status, priorities
from core.serializers import commentsSerializer
from core.serializers import documentsSerializer
from .models import task, hearing


class taskSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    assignee = serializers.SlugRelatedField(
        slug_field='username', many=True, queryset=User.objects.all())
    documents = serializers.SerializerMethodField('get_documents')
    # documents = serializers.SlugRelatedField(slug_field='title', queryset=documents.objects.all())
    comments = serializers.SerializerMethodField('get_comments')
    task_status = serializers.SlugRelatedField(slug_field='status', queryset=Status.objects.all())
    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                              allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                               allow_null=True)
    case_name = serializers.SerializerMethodField('get_case_name')

    class Meta:
        model = task
        fields = ['id', 'title', 'description', 'assignee', 'task_category', 'due_date', 'assign_date', 'comments', 'case_id', 'case_name',
                  'documents', 'folder_id', 'task_status', 'created_by', 'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False}, 'modified_by': {'required': False}}

    def get_case_name(self, obj):
        if obj.case_id:
            try:
                case = LitigationCases.objects.get(id=obj.case_id).name
            except LitigationCases.DoesNotExist:
                case = None
            return case
        else:
            return None

    def get_comments(self, obj):
        return commentsSerializer(obj.comments.filter(is_deleted=False), many=True, read_only=True).data

    def get_documents(self, obj):
        return documentsSerializer(obj.documents.filter(is_deleted=False), many=True, read_only=True).data

    def save(self, *args, **kwargs):
        user = self.context['request'].user
        print(user.id)
        if self.instance.id:
            self.instance.modified_by = user
            self.instance.save()
        else:
            self.instance.created_by = user
        super(taskSerializer, self).save(*args, **kwargs)

    # def update(self, instance, validated_data):
    #     user = self.context['request'].user
    #     validated_data = self.validated_data.items()
    #     self.instance = self.update(self.instance, validated_data)
    #     print(user)
    #     if self.instance.id:
    #         self.instance.modified_by = user
    #         self.instance.save()
    #     else:
    #         self.instance.created_by = user
    #     return self.instance

class OverallStatisticsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    category = serializers.DictField(child=serializers.IntegerField())
    status = serializers.DictField(child=serializers.IntegerField())


class TaskStatisticsSerializer(serializers.Serializer):
    assignee = serializers.CharField()
    total = serializers.IntegerField()
    category = serializers.DictField(child=serializers.IntegerField())
    status = serializers.DictField(child=serializers.IntegerField())

class CombinedStatisticsSerializer(serializers.Serializer):
    overall = OverallStatisticsSerializer()
    assignees = TaskStatisticsSerializer(many=True)



class hearingSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    name = serializers.CharField(max_length=200, required=False, allow_null=True)
    hearing_date = serializers.DateTimeField(required=False, allow_null=True)
    assignee = serializers.SlugRelatedField(
        slug_field='username', many=True, queryset=User.objects.all())
    comments = serializers.SerializerMethodField('get_comments')
    priority = serializers.SlugRelatedField(
        slug_field='priority', queryset=priorities.objects.all())
    court = serializers.SlugRelatedField(slug_field='name', queryset=court.objects.all())
    hearing_status = serializers.SlugRelatedField(slug_field='status', queryset=Status.objects.all())
    documents = serializers.SerializerMethodField('get_documents')
    comments_by_lawyer = serializers.CharField(max_length=200, required=False, allow_null=True)
    case_id = serializers.IntegerField(required=False, allow_null=True)
    folder_id = serializers.IntegerField(required=False, allow_null=True)
    case_name = serializers.SerializerMethodField('get_case_name')
    folder_name = serializers.SerializerMethodField('get_folder_name')
    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                              allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                               allow_null=True)

    def get_case_name(self, obj):
        if obj.case_id:
            try:
                case = LitigationCases.objects.get(id=obj.case_id).name
            except LitigationCases.DoesNotExist:
                case = None
            return case
        else:
            return None

    def get_folder_name(self, obj):
        if obj.folder_id:
            try:
                folder = Folder.objects.get(id=obj.folder_id).name
            except Folder.DoesNotExist:
                folder = None
            return folder
        else:
            return None

    def get_comments(self, obj):
        return commentsSerializer(obj.comments.filter(is_deleted=False), many=True, read_only=True).data

    def get_documents(self, obj):
        return documentsSerializer(obj.documents.filter(is_deleted=False), many=True, read_only=True).data

    class Meta:
        model = hearing
        fields = ['id', 'name', 'hearing_date', 'latest', 'assignee', 'court', 'comments_by_lawyer', 'comments',
                  'documents', 'remind_date',
                  'case_id', 'folder_id', 'folder_name', 'hearing_status', 'case_name', 'priority', 'created_by',
                  'created_at', 'modified_by', 'modified_at', 'remind_me']
        extra_kwargs = {'created_by': {'required': False}, 'modified_by': {'required': False}}

    def save(self, *args, **kwargs):
        user = self.context['request'].user
        if self.instance.id:
            self.instance.modified_by = user
            self.instance.save()
        else:
            self.instance.created_by = user
        super(hearingSerializer, self).save(*args, **kwargs)
