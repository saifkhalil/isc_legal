from accounts.models import User
from django.contrib.auth.models import Group
from rest_framework import serializers
from cases.models import Group
from core.models import comments,replies,priorities,contracts,documents,Status,Path
from drf_dynamic_fields import DynamicFieldsMixin
from pghistory.models import Events
from cases.models import LitigationCases
from rest_framework_recursive.fields import RecursiveField
from django.utils.translation import gettext_lazy as _
from rest_framework.reverse import reverse
from rest_api.relations import FilteredPrimaryKeyRelatedField


# from rest_framework_recursive.fields import RecursiveField
# class FilteredListSerializer(serializers.ListSerializer):

#     def to_representation(self, data):
#         qry_id = self.context['request'].GET.get('pk')
#         print(self.context['request'].data)
#         # if qry_id is not None:
#         #     data = data.filter( is_deleted=False)
#         return super(FilteredListSerializer, self).to_representation(data)

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class repliesSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    
    class Meta:
        # list_serializer_class = FilteredListSerializer
        model = replies
        fields = ['id', 'reply','comment_id','created_by','created_at','modified_by','modified_at']
        extra_kwargs = {'created_by': {'required': False},'modified_by': {'required': False}}

class prioritiesSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = priorities
        fields = ['id', 'priority']


class StatusSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'status']

class contractsSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    attachment = serializers.FileField()
    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    name = serializers.CharField()
    class Meta:
        model = contracts
        # list_serializer_class = FilteredListSerializer
        fields = ['id', 'name','attachment','created_by','created_at','modified_by','modified_at']
        extra_kwargs = {'created_by': {'required': False},'modified_by': {'required': False}}

class documentsSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    attachment = serializers.FileField()
    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    case_name = serializers.SerializerMethodField('get_case_name')

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
        model = documents
        # list_serializer_class = FilteredListSerializer
        fields = ['id', 'name','attachment','case_id','case_name','created_by','created_at','modified_by','modified_at']
        extra_kwargs = {'created_by': {'required': False},'modified_by': {'required': False}}

# class directoriesSerializer(DynamicFieldsMixin,serializers.ModelSerializer):

#     document = documentsSerializer(many=True,read_only=True)
#     # sub_directory = RecursiveField(allow_null=True)
#     class Meta:
#         model = directory
# #        list_serializer_class = FilteredListSerializer
#         fields = [ 'id', 'name','document','sub_directory','created_by','created_at']

# directoriesSerializer._declared_fields['sub_directory'] = directoriesSerializer()


class commentsSerializer(DynamicFieldsMixin,serializers.ModelSerializer):    
    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all(),required=False, allow_null=True)
    replies = serializers.SerializerMethodField('get_replis')

    def get_replis(self, obj):
        # You can do more complex filtering stuff here.
        return repliesSerializer(obj.replies.filter(is_deleted=False), many=True, read_only=True).data

    class Meta:
        ref_name = 'Comments'
        # list_serializer_class = FilteredListSerializer
        model = comments
        fields = ['id', 'comment','replies','case_id','folder_id','event_id','task_id','hearing_id','created_by','created_at','modified_by','modified_at']
        extra_kwargs = {'created_by': {'required': False},'modified_by': {'required': False}}

class EventsSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = Events
        # list_serializer_class = FilteredListSerializer
        fields = ['pgh_diff',]

class PathSerializer(serializers.ModelSerializer):
    children = RecursiveField(
        help_text=_('List of children paths.'), label=_('Children'),
        many=True, read_only=True
    )
    # documents_url = serializers.HyperlinkedIdentityField(
    #     help_text=_(
    #         'URL of the API endpoint showing the list documents inside this '
    #         'path.'
    #     ), label=_('Documents URL'), lookup_url_kwarg='path_id',
    #     view_name='path-document-list'
    # )

    documents = documentsSerializer(many=True,read_only=True)

    # full_path = serializers.SerializerMethodField(
    #     help_text=_(
    #         'The name of this path level appended to the names of its '
    #         'ancestors.'
    #     ), label=_('Full path'), read_only=True
    # )
    # parent_url = serializers.SerializerMethodField(
    #     label=_('Parents URL'), read_only=True
    # )

    # This is here because parent is optional in the model but the serializer
    # sets it as required.
    # parent = serializers.PrimaryKeyRelatedField(
    #     allow_null=True, label=_('Parent'), queryset=Path.objects.all(),
    #     required=False
    # )

    # DEPRECATION: Version 5.0, remove 'parent' fields from GET request as
    # it is replaced by 'parent_id'.

    class Meta:
        extra_kwargs = {
            'url': {
                'label': _('URL'),
                'lookup_url_kwarg': 'path_id',
                'view_name': 'path-detail'
            }
        }
        fields = (
            'children', 'id', 'name','parent', 
            'parent_id','documents'
            # 'parent_url', 'url','full_path', 'documents_url',
        )
        model = Path
        read_only_fields = (
            'children', 'id',
            'parent_id',
             'parent_url', 'url', 'full_path', 'documents_url','documents'
        )

    # def get_full_path(self, obj):
    #     return obj.name

    # def get_parent_url(self, obj):
    #     if obj.parent:
    #         return reverse(
    #             viewname='path-detail',
    #             kwargs={'path_id': obj.parent.pk},
    #             format=self.context['format'],
    #             request=self.context.get('request')
    #         )
    #     else:
    #         return ''


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
