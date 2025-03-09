from django.shortcuts import get_object_or_404
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from accounts.models import User, Employees
from cases.models import (
    LitigationCases,
    stages,
    client_position,
    opponent_position,
    case_type,
    court,
    Folder,
    ImportantDevelopment,
    AdministrativeInvestigation,
    Notation, characteristic
)
from core.models import Status, priorities
from core.serializers import commentsSerializer, documentsSerializer, PathSerializer
from django.core.cache import cache


class case_typeSerializer(serializers.ModelSerializer):
    class Meta:
        model = case_type
        fields = ['id', 'type']


class client_positionSerializer(serializers.ModelSerializer):
    class Meta:
        model = client_position
        fields = ['id', 'name']


class opponent_positionSerializer(serializers.ModelSerializer):
    class Meta:
        model = opponent_position
        fields = ['id', 'position']


class opponent_positionSerializer(serializers.ModelSerializer):
    class Meta:
        model = opponent_position
        fields = ['id', 'position']


class courtSerializer(serializers.ModelSerializer):
    class Meta:
        model = court
        fields = ['id', 'name']


class stagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = stages
        fields = ['id', 'name']


class characteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = characteristic
        fields = ['id', 'name']


class ImportantDevelopmentsSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all())

    class Meta:
        model = ImportantDevelopment
        fields = ['id', 'title', 'case_id', 'folder_id', 'admin_id', 'notation_id', 'contract_id', 'created_at',
                  'created_by']


class LitigationCasesSerializer_OLD(DynamicFieldsMixin, serializers.ModelSerializer):
    court = serializers.SlugRelatedField(
        slug_field='name', queryset=court.objects.all(), required=False)
    case_status = serializers.SlugRelatedField(
        slug_field='status', queryset=Status.objects.all())
    priority = serializers.SlugRelatedField(
        slug_field='priority', queryset=priorities.objects.all())
    case_type = serializers.SlugRelatedField(
        slug_field='type', queryset=case_type.objects.all())

    client_position = serializers.SlugRelatedField(
        slug_field='name', queryset=client_position.objects.all(), required=False)
    opponent_position = serializers.SlugRelatedField(
        slug_field='position', queryset=opponent_position.objects.all(), required=False)
    Stage = serializers.SlugRelatedField(
        slug_field='name', queryset=stages.objects.all(), required=False)
    characteristic = serializers.SlugRelatedField(
        slug_field='name', queryset=characteristic.objects.all(), required=False)
    assignee = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all())
    comments = serializers.SerializerMethodField('get_comments')
    documents = serializers.SerializerMethodField()
    paths = PathSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField('get_tasks')
    ImportantDevelopment = serializers.SerializerMethodField()
    hearing = serializers.SerializerMethodField()
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    created_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                              slug_field='username', read_only=True)
    modified_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                               slug_field='username', read_only=True)

    def get_tasks(self, obj):
        if obj.id:
            pk = self.kwargs.get("pk")
            case_cache_key = f"litigation_case_{pk}"
            cached_case = cache.get(case_cache_key)
            if cached_case:
                case = cached_case
            else:
                case = get_object_or_404(LitigationCases, pk=pk)
                cache.set(cache_key, obj, 60 * 60)
            cache_key = f"case_{obj.id}_tasks_queryset"
            cached_queryset = cache.get(cache_key)
            if cached_queryset:
                result = cached_queryset
            else:
                result = case.tasks.all().filter(is_deleted=False).values()
                cache.set(cache_key, result, timeout=600)
            return result


    def get_hearing(self, obj):
        if obj.id:
            pk = self.kwargs.get("pk")
            case_cache_key = f"litigation_case_{pk}"
            cached_case = cache.get(case_cache_key)
            if cached_case:
                case = cached_case
            else:
                case = get_object_or_404(LitigationCases, pk=pk)
                cache.set(cache_key, obj, 60 * 60)
            cache_key = f"case_{obj.id}_hearing_queryset"
            cached_queryset = cache.get(cache_key)
            if cached_queryset:
                result = cached_queryset
            else:
                result = case.hearing.all().filter(is_deleted=False).values()
                cache.set(cache_key, result, timeout=600)
            return result

    def get_documents(self, obj):
        if obj.id:
            case = get_object_or_404(LitigationCases, pk=obj.id)
            cache_key = f"case_{obj.id}_documents_queryset"
            cached_queryset = cache.get(cache_key)
            if cached_queryset:
                result = cached_queryset
            else:
                result = case.documents.all().filter(is_deleted=False).values()
                cache.set(cache_key, result, timeout=600)
            return result

    def get_comments(self, obj):
        return commentsSerializer(obj.comments.filter(is_deleted=False), many=True, read_only=True).data

    def get_ImportantDevelopment(self, obj):
        return ImportantDevelopmentsSerializer(obj.ImportantDevelopment.filter(is_deleted=False), many=True,
                                               read_only=True).data

    class Meta:
        model = LitigationCases
        fields = ['id', 'name', 'description', 'case_category', 'priority', 'shared_with', 'court',
                  'ImportantDevelopment', 'case_type', 'case_status', 'judge', 'detective', 'client_position',
                  'opponent_position', 'assignee', 'Stage', 'characteristic', 'internal_ref_number', 'comments',
                  'tasks', 'documents',
                  'case_close_status', 'case_close_comment',
                  'paths', 'hearing', 'start_time', 'end_time', 'created_by', 'created_at', 'modified_by',
                  'modified_at']
        http_method_names = ['get', 'post', 'head', 'put']


class LitigationCasesSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    court = serializers.SlugRelatedField(
        slug_field='name', queryset=court.objects.only('name'), required=False
    )
    case_status = serializers.SlugRelatedField(
        slug_field='status', queryset=Status.objects.only('status')
    )
    priority = serializers.SlugRelatedField(
        slug_field='priority', queryset=priorities.objects.only('priority')
    )
    case_type = serializers.SlugRelatedField(
        slug_field='type', queryset=case_type.objects.only('type')
    )
    client_position = serializers.SlugRelatedField(
        slug_field='name', queryset=client_position.objects.only('name'), required=False
    )
    opponent_position = serializers.SlugRelatedField(
        slug_field='position', queryset=opponent_position.objects.only('position'), required=False
    )
    Stage = serializers.SlugRelatedField(
        slug_field='name', queryset=stages.objects.only('name'), required=False
    )
    characteristic = serializers.SlugRelatedField(
        slug_field='name', queryset=characteristic.objects.only('name'), required=False
    )
    assignee = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.only('username')
    )

    # Optimized serializer fields using SerializerMethodField
    comments = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    paths = PathSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()
    ImportantDevelopment = serializers.SerializerMethodField()
    hearing = serializers.SerializerMethodField()

    # Date fields with formatted output
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)

    # User fields
    created_by = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username', read_only=True
    )
    modified_by = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username', read_only=True
    )

    def get_cached_queryset(self, obj, related_field, cache_suffix):
        """Helper function to fetch cached queryset"""
        if not obj.id:
            return []

        cache_key = f"case_{obj.id}_{cache_suffix}_queryset"
        cached_queryset = cache.get(cache_key)

        if cached_queryset is None:
            result = getattr(obj, related_field).filter(is_deleted=False).values()
            cache.set(cache_key, result, timeout=600)
        else:
            result = cached_queryset

        return result

    def get_tasks(self, obj):
        return self.get_cached_queryset(obj, "tasks", "tasks")

    def get_hearing(self, obj):
        return self.get_cached_queryset(obj, "hearing", "hearing")

    def get_documents(self, obj):
        return self.get_cached_queryset(obj, "documents", "documents")

    def get_comments(self, obj):
        return commentsSerializer(
            obj.comments.filter(is_deleted=False), many=True, read_only=True
        ).data

    def get_ImportantDevelopment(self, obj):
        return ImportantDevelopmentsSerializer(
            obj.ImportantDevelopment.filter(is_deleted=False), many=True, read_only=True
        ).data

    class Meta:
        model = LitigationCases
        fields = [
            'id', 'name', 'description', 'case_category', 'priority', 'shared_with', 'court',
            'ImportantDevelopment', 'case_type', 'case_status', 'judge', 'detective',
            'client_position', 'opponent_position', 'assignee', 'Stage', 'characteristic',
            'internal_ref_number', 'comments', 'tasks', 'documents', 'case_close_status',
            'case_close_comment', 'paths', 'hearing', 'start_time', 'end_time', 'created_by',
            'created_at', 'modified_by', 'modified_at'
        ]
        http_method_names = ['get', 'post', 'head', 'put']

class OverallStatisticsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    status = serializers.DictField(child=serializers.IntegerField())
    case_close_status = serializers.DictField(child=serializers.IntegerField())
    case_type = serializers.DictField(child=serializers.IntegerField())
    court = serializers.DictField(child=serializers.IntegerField())


class LitigationCaseStatisticsSerializer(serializers.Serializer):
    assignee = serializers.CharField()
    total = serializers.IntegerField()
    status = serializers.DictField(child=serializers.IntegerField())
    case_close_status = serializers.DictField(child=serializers.IntegerField())
    case_type = serializers.DictField(child=serializers.IntegerField())
    court = serializers.DictField(child=serializers.IntegerField())


class CombinedStatisticsSerializer(serializers.Serializer):
    overall = OverallStatisticsSerializer()
    assignees = LitigationCaseStatisticsSerializer(many=True)


class FoldersSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    court = serializers.SlugRelatedField(
        slug_field='name', queryset=court.objects.all(), required=False)
    priority = serializers.SlugRelatedField(
        slug_field='priority', queryset=priorities.objects.all(), required=False)
    folder_type = serializers.SlugRelatedField(
        slug_field='type', queryset=case_type.objects.all(), required=False)
    assignee = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(), required=False)
    comments = serializers.SerializerMethodField('get_comments')
    documents = documentsSerializer(many=True, read_only=True)
    paths = PathSerializer(many=True, read_only=True)
    hearing = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField('get_tasks')
    ImportantDevelopment = serializers.SerializerMethodField()
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    created_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                              slug_field='username', read_only=True)
    modified_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                               slug_field='username', read_only=True)

    def get_tasks(self, obj):
        if obj.id:
            folder = get_object_or_404(Folder, pk=obj.id)
            result = folder.tasks.all().filter(is_deleted=False).values()
            return result

    def get_hearing(self, obj):
        if obj.id:
            folder = get_object_or_404(Folder, pk=obj.id)
            result = folder.hearing.all().filter(is_deleted=False).values()
            return result

    def get_comments(self, obj):
        return commentsSerializer(obj.comments.filter(is_deleted=False), many=True, read_only=True).data

    def get_ImportantDevelopment(self, obj):
        return ImportantDevelopmentsSerializer(obj.ImportantDevelopment.filter(is_deleted=False), many=True,
                                               read_only=True).data

    class Meta:
        model = Folder
        fields = ['id', 'name', 'description', 'folder_category', 'record_type', 'priority', 'shared_with', 'court',
                  'ImportantDevelopment', 'folder_type', 'folder_status', 'assignee', 'internal_ref_number', 'comments',
                  'tasks', 'documents', 'paths', 'hearing', 'start_time', 'end_time', 'created_by', 'created_at',
                  'modified_by', 'modified_at']
        http_method_names = ['get', 'post', 'head', 'put']


class AdministrativeInvestigationsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    priority = serializers.SlugRelatedField(
        slug_field='priority', queryset=priorities.objects.all())
    chairman = serializers.SlugRelatedField(
        slug_field='full_name', queryset=Employees.objects.all(), required=False)
    assignee = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all())
    members = serializers.SlugRelatedField(
        slug_field='full_name', many=True, queryset=Employees.objects.all(), required=False)
    shared_with = serializers.SlugRelatedField(
        slug_field='username', many=True, queryset=User.objects.all())
    paths = PathSerializer(many=True, read_only=True)
    ImportantDevelopment = serializers.SerializerMethodField()
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    created_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                              slug_field='username', read_only=True)
    modified_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                               slug_field='username', read_only=True)

    def get_full_names(self, obj):
        result = [f'{user.first_name} {user.last_name}' for user in User.objects.all()]
        return result

    def get_ImportantDevelopment(self, obj):
        return ImportantDevelopmentsSerializer(obj.ImportantDevelopment.filter(is_deleted=False), many=True,
                                               read_only=True).data

    class Meta:
        model = AdministrativeInvestigation
        fields = ['id', 'subject', 'admin_order_number', 'chairman', 'priority', 'members', 'paths', 'shared_with',
                  'assignee', 'start_time', 'end_time', 'ImportantDevelopment', 'is_deleted', 'created_by',
                  'created_at', 'modified_by', 'modified_at']
        http_method_names = ['get', 'post', 'head', 'put']


class NotationSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    priority = serializers.SlugRelatedField(
        slug_field='priority', queryset=priorities.objects.all())
    comments = serializers.SerializerMethodField('get_comments')
    court = serializers.SlugRelatedField(
        slug_field='name', queryset=court.objects.all(), required=False)
    paths = PathSerializer(many=True, read_only=True)
    ImportantDevelopment = serializers.SerializerMethodField()
    assignee = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all(), required=False)
    reference_date = serializers.DateField(format="%Y-%m-%d", required=False)
    notation_date = serializers.DateField(format="%Y-%m-%d", required=False)
    start_time = serializers.DateField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateField(format="%Y-%m-%d", required=False)
    created_by = serializers.SlugRelatedField(
        slug_field='username', read_only=True)
    modified_by = serializers.SlugRelatedField(
        slug_field='username', read_only=True)

    def get_comments(self, obj):
        return commentsSerializer(obj.comments.filter(is_deleted=False), many=True, read_only=True).data

    def get_ImportantDevelopment(self, obj):
        return ImportantDevelopmentsSerializer(obj.ImportantDevelopment.filter(is_deleted=False), many=True,
                                               read_only=True).data

    class Meta:
        model = Notation
        fields = ['id', 'subject', 'description', 'reference_number', 'reference_date', 'notation_date', 'paths',
                  'requester',
                  'court', 'judge', 'detective', 'authorized_number', 'ImportantDevelopment', 'shared_with', 'comments',
                  'priority', 'start_time', 'end_time', 'is_deleted', 'created_by', 'created_at', 'modified_by',
                  'modified_at', 'assignee']
        http_method_names = ['get', 'post', 'head', 'put']
