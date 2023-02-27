from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from drf_dynamic_fields import DynamicFieldsMixin
from pghistory.models import Events
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_recursive.fields import RecursiveField

from accounts.models import User
from cases.models import LitigationCases
from core.models import comments, replies, priorities, contracts, documents, Status, Path
from rest_api.relations import FilteredPrimaryKeyRelatedField


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class repliesSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                              allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                               allow_null=True)

    class Meta:
        model = replies
        fields = ['id', 'reply', 'comment_id', 'created_by', 'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False}, 'modified_by': {'required': False}}


class prioritiesSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = priorities
        fields = ['id', 'priority']


class StatusSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'status']


class contractsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    attachment = serializers.FileField()
    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                              allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                               allow_null=True)
    name = serializers.CharField()

    class Meta:
        model = contracts
        fields = ['id', 'name', 'attachment', 'created_by', 'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False}, 'modified_by': {'required': False}}


class documentsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    attachment = serializers.FileField()
    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                              allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                               allow_null=True)
    case_name = serializers.SerializerMethodField('get_case_name')
    path_name = serializers.SerializerMethodField('get_path_name')

    def get_case_name(self, obj):
        if obj.case_id:
            try:
                case = LitigationCases.objects.get(id=obj.case_id).name
            except LitigationCases.DoesNotExist:
                case = None
            return case
        else:
            return None

    def get_path_name(self, obj):
        if obj.path_id:
            try:
                path = Path.objects.get(id=obj.path_id).name
            except Path.DoesNotExist:
                path = None
            return path
        else:
            return None

    class Meta:
        model = documents
        fields = ['id', 'name', 'attachment', 'case_id', 'case_name', 'path_id', 'path_name', 'created_by',
                  'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False}, 'modified_by': {'required': False}}


class commentsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                              allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                               allow_null=True)
    replies = serializers.SerializerMethodField('get_replis')

    def get_replis(self, obj):
        # You can do more complex filtering stuff here.
        return repliesSerializer(obj.replies.filter(is_deleted=False), many=True, read_only=True).data

    class Meta:
        ref_name = 'Comments'
        # list_serializer_class = FilteredListSerializer
        model = comments
        fields = ['id', 'comment', 'replies', 'case_id', 'folder_id', 'event_id', 'task_id', 'hearing_id', 'created_by',
                  'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False}, 'modified_by': {'required': False}}


class EventsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Events
        # list_serializer_class = FilteredListSerializer
        fields = ['pgh_diff', ]


class PathSerializer(serializers.ModelSerializer):
    case_name = serializers.SerializerMethodField('get_case_name')
    subPaths = RecursiveField(
        help_text=_('List of Sub-paths.'), label=_('SubPaths'),
        many=True, read_only=True, source='active_path'
    )
    documents = documentsSerializer(many=True, read_only=True)

    def get_case_name(self, obj):
        if obj.case_id:
            try:
                case = LitigationCases.objects.get(id=obj.case_id).name
            except LitigationCases.DoesNotExist:
                case = None
            return case
        else:
            return None

    class Meta:
        extra_kwargs = {
            'url': {
                'label': _('URL'),
                'lookup_url_kwarg': 'path_id',
                'view_name': 'path-detail'
            }
        }
        validators = [
            UniqueTogetherValidator(
                queryset=Path.objects.all(),
                fields=('name', 'parent'),
                message="اسم المجلد موجود مسبقا"
            )
        ]
        fields = (
            'subPaths', 'id', 'name', 'parent', 'case_id', 'case_name', 'folder_id',
            'parent_id', 'documents'
            # 'parent_url', 'url','full_path', 'documents_url',
        )
        model = Path
        read_only_fields = (
            'subPaths', 'id', 'case_name',
            'parent_id',
            'parent_url', 'url', 'full_path', 'documents_url', 'documents'
        )


class PathDocumentAddSerializer(serializers.Serializer):
    document = FilteredPrimaryKeyRelatedField(
        help_text=_(
            'Primary key of the document to add to the Path.'
        ), label=_('Document ID'), source_queryset=documents.objects.all()
    )


class PathDocumentRemoveSerializer(serializers.Serializer):
    document = FilteredPrimaryKeyRelatedField(
        help_text=_(
            'Primary key of the document to remove from the Path.'
        ), label=_('Document ID'), source_queryset=documents.objects.all()
    )
