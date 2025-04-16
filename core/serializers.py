from auditlog.models import LogEntry
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from drf_dynamic_fields import DynamicFieldsMixin
from pghistory.models import Events
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_recursive.fields import RecursiveField
from django.db.models import Q

from accounts.models import User
from cases.models import LitigationCases, Notation, AdministrativeInvestigation, Folder
from contract.models import Contract
from core.models import comments, replies, priorities, contracts, documents, Status, Path, Notification
from rest_api.relations import FilteredPrimaryKeyRelatedField
from django.core.cache import cache

class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class LogEntrySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    model = serializers.SlugRelatedField(source='content_type',
                                         queryset=ContentType.objects.all(),
                                         slug_field='model',
                                         )
    action = serializers.CharField(source='get_action_display')
    object_name = serializers.SerializerMethodField('get_object_name')
    actor = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username', read_only=True
    )

    # def get_changes(self, obj):
    #     return json.loads(obj.changes)
    def get_object_name(self, obj):
        ct = ContentType.objects.get_for_id(obj.content_type.id)
        obj = ct.get_object_for_this_type(pk=obj.object_id)
        return str(obj)

    class Meta:
        model = LogEntry
        fields = ['model', 'object_id', 'object_name', 'action', 'remote_addr', 'changes', 'actor', 'timestamp', ]
        http_method_names = ['get', 'head']


class LogEntryInObjectSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    action = serializers.CharField(source='get_action_display')
    # changes = serializers.SerializerMethodField('get_changes')
    actor = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username', read_only=True
    )

    # def get_changes(self, obj):
    #     return json.loads(obj.changes)

    class Meta:
        model = LogEntry
        fields = ['action', 'changes', 'actor', 'timestamp']
        http_method_names = ['get', 'head']


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
        fields = ['id', 'reply', 'comment_id', 'created_by',
                  'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False},
                        'modified_by': {'required': False}}


class prioritiesSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = priorities
        fields = ['id', 'priority']


class StatusSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'status', 'is_completed', 'is_done']


class contractsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    attachment = serializers.FileField()
    created_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                              allow_null=True)
    modified_by = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False,
                                               allow_null=True)
    name = serializers.CharField()

    class Meta:
        model = contracts
        fields = ['id', 'name', 'attachment', 'created_by',
                  'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False},
                        'modified_by': {'required': False}}


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
        fields = ['id', 'name', 'attachment', 'case_id', 'case_name', 'path_id', 'path_name', 'task_id', 'hearing_id',
                  'created_by', 'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False},
                        'modified_by': {'required': False}}


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
        fields = ['id', 'comment', 'replies', 'case_id', 'folder_id', 'event_id', 'task_id', 'hearing_id', 'contract_id',
                  'notation_id', 'created_by',
                  'created_at', 'modified_by', 'modified_at']
        extra_kwargs = {'created_by': {'required': False},
                        'modified_by': {'required': False}}


class EventsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Events
        # list_serializer_class = FilteredListSerializer
        fields = ['pgh_diff', ]


class CustomRecursiveField(serializers.ListSerializer):
    def to_representation(self, data):
        return super().to_representation(data)


class PathSerializer_old(serializers.ModelSerializer):
    case_name = serializers.SerializerMethodField('get_case_name')
    admin_name = serializers.SerializerMethodField('get_admin_name')
    notation_name = serializers.SerializerMethodField('get_notation_name')
    folder_name = serializers.SerializerMethodField('get_folder_name')
    contract_name = serializers.SerializerMethodField('get_contract_name')
    # subPaths = RecursiveField(
    #     help_text=_('List of Sub-paths.'), label=_('SubPaths'),
    #     many=True, read_only=True, source='get_children'
    # )
    # children = CustomRecursiveField(child=RecursiveField(), read_only=True)
    subPaths = RecursiveField(source='children', many=True)
    # filtered_children = RecursiveField(many=True)
    created_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                              slug_field='username', read_only=True)
    documents = documentsSerializer(many=True, read_only=True)

    # subPaths = RecursiveField(
    #     help_text=_('List of Sub-paths.'), label=_('SubPaths'),
    #     many=True, read_only=True, source='get_filtered_children')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Retrieve the request object if provided
        super(PathSerializer, self).__init__(*args, **kwargs)


    def to_representation(self, instance):
        data = super().to_representation(instance)
        current_user = self.context['request'].user
        limit = int(self.context['request'].query_params.get('limit', 10))  # Default to 10 if not specified
        skip = int(self.context['request'].query_params.get('skip', 0))  # Default to 0 if not specified
        parent_node = instance
        if parent_node.id in (1, 24):
            if current_user.is_manager or current_user.is_superuser or (current_user.is_cases_public_manager and current_user.is_cases_private_manager):
                children = parent_node.get_children()
            elif current_user.is_contract_manager and parent_node.id == 24:
                children = parent_node.get_children()
            elif current_user.is_cases_private_manager:
                filter_query = Q(assignee__exact=current_user) | Q(
                    created_by__exact=current_user) | Q(shared_with__exact=current_user)
                cases_filter = filter_query | Q(case_category='Private')
                cases = LitigationCases.objects.filter(cases_filter)
                cases_ids = cases.values_list('id', flat=True)
                child_filter_query = Q(created_by__exact=current_user) | Q(case_id__in=cases_ids)
                children = parent_node.get_children().filter(child_filter_query).distinct()
            elif current_user.is_cases_public_manager:
                filter_query = Q(assignee__exact=current_user) | Q(
                    created_by__exact=current_user) | Q(shared_with__exact=current_user)
                cases_filter = filter_query | Q(case_category='Public')
                cases = LitigationCases.objects.filter(cases_filter)
                cases_ids = cases.values_list('id', flat=True)
                child_filter_query = Q(created_by__exact=current_user) | Q(case_id__in=cases_ids)
                children = parent_node.get_children().filter(child_filter_query).distinct()
            else:
                filter_query = Q(assignee__exact=current_user) | Q(
                    created_by__exact=current_user) | Q(shared_with__exact=current_user)
                cases = LitigationCases.objects.filter(filter_query).distinct()
                admins = AdministrativeInvestigation.objects.filter(filter_query).distinct()
                notations = Notation.objects.filter(filter_query).distinct()
                folders = Folder.objects.filter(filter_query).distinct()
                contracts = Contract.objects.filter(filter_query).distinct()
                cases_ids = cases.values_list('id', flat=True)
                admins_ids = admins.values_list('id', flat=True)
                notations_ids = notations.values_list('id', flat=True)
                folders_ids = folders.values_list('id', flat=True)
                contracts_ids = contracts.values_list('id', flat=True)
                child_filter_query = Q(created_by__exact=current_user) | Q(case_id__in=cases_ids) | Q(admin_id__in=admins_ids) | Q(notation_id__in=notations_ids) | Q(folder_id__in=folders_ids) | Q(contract_id__in=contracts_ids)
                # queryset = queryset.filter(filter_query).distinct()
                children = parent_node.get_children().filter(child_filter_query).distinct()
            children_data = []
            children = children[skip:skip + limit]
            # for child in instance.get_children():
            #     child_serializer = self.__class__(child, context=self.context)
            #     children_data.append(child_serializer.data)
            # filtered_children = children
            if children:
                # child_serializer = self.__class__(context=self.context)
                children_data = [self.__class__(child, context=self.context).data for child in children]
                # for child in children:
                #     child_serializer = self.__class__(child, context=self.context)
                #     children_data.append(child_serializer.data)
            data['subPaths'] = children_data
        return data

    def get_filtered_children(self, obj):
        children_data = []
        # Access the filtered_children attribute from the parent object
        filtered_children = getattr(obj, 'filtered_children', None)
        # for child in filtered_children:
        #     child_serializer = self.__class__(child, context=self.context)
        #     children_data.append(child_serializer.data)
        # data['children'] = children_data
        # You can serialize the filtered_children here if needed
        # For example, you can use another serializer if filtered_children are models
        filtered_children_data = PathSerializer(filtered_children, many=True).data

        return filtered_children_data

    def get_case_name(self, obj):
        if obj.case_id:
            try:
                case = LitigationCases.objects.get(id=obj.case_id).name
            except LitigationCases.DoesNotExist:
                case = None
            return case
        else:
            return None

    def get_admin_name(self, obj):
        if obj.admin_id:
            try:
                admin = AdministrativeInvestigation.objects.get(id=obj.admin_id).subject
            except AdministrativeInvestigation.DoesNotExist:
                admin = None
            return admin
        else:
            return None

    def get_notation_name(self, obj):
        if obj.notation_id:
            try:
                notation = Notation.objects.get(id=obj.notation_id).subject
            except Notation.DoesNotExist:
                notation = None
            return notation
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

    def get_contract_name(self, obj):
        if obj.contract_id:
            try:
                contract = Contract.objects.get(id=obj.contract_id).name
            except Contract.DoesNotExist:
                contract = None
            return contract
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
            'subPaths', 'id', 'name', 'parent', 'case_id', 'case_name', 'folder_id', 'folder_name', 'admin_id',
            'admin_name', 'notation_id', 'notation_name', 'contract_id', 'contract_name', 'parent_id', 'documents', 'created_by',
            # 'parent_url', 'url','full_path', 'documents_url',
        )
        model = Path
        read_only_fields = (
           'subPaths',  'id', 'case_name',
            'parent_id',
            'parent_url', 'url', 'full_path', 'documents_url', 'documents', 'created_by'
        )


class PathSerializer(serializers.ModelSerializer):
    case_name = serializers.SerializerMethodField()
    admin_name = serializers.SerializerMethodField()
    notation_name = serializers.SerializerMethodField()
    folder_name = serializers.SerializerMethodField()
    contract_name = serializers.SerializerMethodField()
    subPaths = serializers.SerializerMethodField()
    documents = documentsSerializer(many=True, read_only=True)

    created_by = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field="username",
        read_only=True
    )

    def get_cached_related_name(self, obj, related_model, field_name,field, cache_suffix):
        """Helper function to fetch cached related name."""
        if not getattr(obj, field, None):
            return None

        cache_key = f"{related_model}_{field}_{getattr(obj, field_name)}"
        cached_name = cache.get(cache_key)

        if cached_name is None:
            try:
                field_n = field
                field_object = related_model._meta.get_field(field)
                related_obj = related_model.objects.only(field).get(id=obj.id)
                cached_name = getattr(related_obj,field_object.attname)
                cache.set(cache_key, cached_name, timeout=None)
            except related_model.DoesNotExist:
                cached_name = None

        return cached_name

    def get_case_name(self, obj):
        return self.get_cached_related_name(obj=obj, related_model=LitigationCases, field_name="case_id", cache_suffix="case",field="name")

    def get_admin_name(self, obj):
        return self.get_cached_related_name(obj=obj, related_model=AdministrativeInvestigation, field_name="admin_id", cache_suffix="admin",field="subject")

    def get_notation_name(self, obj):
        return self.get_cached_related_name(obj=obj,related_model= Notation, field_name="notation_id", cache_suffix="notation",field="subject")

    def get_folder_name(self, obj):
        return self.get_cached_related_name(obj=obj, related_model=Folder, field_name="folder_id", cache_suffix="folder",field="name")

    def get_contract_name(self, obj):
        return self.get_cached_related_name(obj=obj, related_model=Contract, field_name="contract_id", cache_suffix="contract",field="name")

    def get_subPaths(self, obj):
        """Retrieves cached children nodes based on user permissions."""
        request = self.context.get("request")
        if not request:
            return []

        current_user = request.user
        cache_key = f"path_{obj.id}_children_{current_user.id}"
        cached_children = cache.get(cache_key)

        if cached_children is None:
            children_query = obj.get_children()

            if not current_user.is_superuser and not current_user.is_manager:
                filter_query = Q(created_by=current_user) | Q(shared_with=current_user) | Q(assignee=current_user)
                cases = LitigationCases.objects.filter(filter_query).values_list("id", flat=True)
                child_filter_query = Q(created_by=current_user) | Q(case_id__in=cases)
                children_query = children_query.filter(child_filter_query).distinct()

            children_data = PathSerializer(children_query, many=True, context=self.context).data
            cache.set(cache_key, children_data, timeout=None)
        else:
            children_data = cached_children

        return children_data

    class Meta:
        model = Path
        fields = [
            "id", "name", "parent", "case_id", "case_name", "folder_id", "folder_name",
            "admin_id", "admin_name", "notation_id", "notation_name", "contract_id", "contract_name",
            "parent_id", "documents", "subPaths", "created_by"
        ]
        read_only_fields = ["id", "subPaths", "case_name", "created_by"]

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


class NotificationSerializer(serializers.ModelSerializer):
    content_type = serializers.SlugRelatedField(
        slug_field='model', queryset=ContentType.objects.all(), required=True, allow_null=False)
    action_by = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'content_type', 'action_by', 'action_at',
                  'object_id', 'object_name', 'role', 'action', 'is_read', 'browser_read', 'user']

    def get_action_by(self, obj):
        return obj.action_by.username if obj.action_by else None

    def get_user(self, obj):
        return obj.user.username if obj.user else None



class YourMPTTModelSerializer(serializers.ModelSerializer):
    subPaths = serializers.SerializerMethodField()
    documents = documentsSerializer(many=True, read_only=True)
    case_name = serializers.SerializerMethodField('get_case_name')
    admin_name = serializers.SerializerMethodField('get_admin_name')
    notation_name = serializers.SerializerMethodField('get_notation_name')
    folder_name = serializers.SerializerMethodField('get_folder_name')
    created_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                              slug_field='username', read_only=True)

    class Meta:
        model = Path
        fields = (
            'id', 'name', 'parent', 'case_id', 'case_name', 'folder_id', 'folder_name', 'admin_id',
            'admin_name', 'notation_id', 'notation_name', 'parent_id','created_by', 'documents', 'subPaths',
            # 'parent_url', 'url','full_path', 'documents_url',
        )

    def get_subPaths(self, obj):
        children = Path.objects.filter(parent=obj)
        return children  # Return the queryset directly

    def get_case_name(self, obj):
        if obj.case_id:
            try:
                case = LitigationCases.objects.get(id=obj.case_id).name
            except LitigationCases.DoesNotExist:
                case = None
            return case
        else:
            return None

    def get_admin_name(self, obj):
        if obj.admin_id:
            try:
                admin = AdministrativeInvestigation.objects.get(id=obj.admin_id).subject
            except AdministrativeInvestigation.DoesNotExist:
                admin = None
            return admin
        else:
            return None

    def get_notation_name(self, obj):
        if obj.notation_id:
            try:
                notation = Notation.objects.get(id=obj.notation_id).subject
            except Notation.DoesNotExist:
                notation = None
            return notation
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

