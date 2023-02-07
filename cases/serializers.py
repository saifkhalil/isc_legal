from core.models import priorities
from rest_framework import serializers,status
from rest_framework.response import Response
from drf_dynamic_fields import DynamicFieldsMixin
from .models import LitigationCases,stages,client_position,opponent_position,Group,case_type,court,LitigationCasesEvent,Folder,ImportantDevelopment
from core.serializers import commentsSerializer,documentsSerializer,StatusSerializer,PathSerializer
from accounts.models import User
from activities.models import task,hearing
from activities.serializers import hearingSerializer,taskSerializer
# from core.serializers import FilteredListSerializer
import json
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict


class case_typeSerializer(serializers.ModelSerializer):
    class Meta:
        model = case_type
        fields = ['id', 'type']

# class companySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = company
#         fields = ['id', 'full_name','name','foreign_name','category_id','sub_category_id','company_legal_type_id','company_group_id','reference']

# class personsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = persons
#         fields = ['id', 'name']


class client_positionSerializer(serializers.ModelSerializer):
    class Meta:
        model = client_position
        fields = ['id', 'name']


class opponent_positionSerializer(serializers.ModelSerializer):
    class Meta:
        model = opponent_position
        fields = ['id', 'position']



# class opponentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = client_position
#         fields = ['id', 'name']


class opponent_positionSerializer(serializers.ModelSerializer):
    class Meta:
        model = opponent_position
        fields = ['id', 'position']

class courtSerializer(serializers.ModelSerializer):
    class Meta:
        model = court
        fields = ['id', 'name']

# class assigned_teamSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Group
#         fields = ['id', 'name']

class stagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = stages
        fields = ['id', 'name']

class ImportantDevelopmentsSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all())

    class Meta:
        model = ImportantDevelopment
        fields = ['id', 'title','case_id','created_at','created_by']

class LitigationCasesEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LitigationCasesEvent
        fields = '__all__'
        http_method_names = ['get',]

class LitigationCasesSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    court = serializers.SlugRelatedField(slug_field='name',queryset=court.objects.all())
    priority = serializers.SlugRelatedField(slug_field='priority',queryset=priorities.objects.all())
    case_type = serializers.SlugRelatedField(slug_field='type',queryset=case_type.objects.all())
    client_position = serializers.SlugRelatedField(slug_field='name',queryset=client_position.objects.all())
    opponent_position = serializers.SlugRelatedField(slug_field='position',queryset=opponent_position.objects.all())
    Stage = serializers.SlugRelatedField(slug_field='name',queryset=stages.objects.all())
    assignee = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all())
    comments = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    paths = PathSerializer(many=True,read_only=True )
    tasks = serializers.SerializerMethodField('get_tasks')
    # tasks = taskSerializer(task.objects.filter(is_deleted=True).order_by('-id'), many=True,read_only=True)
    ImportantDevelopment = ImportantDevelopmentsSerializer(many=True,read_only=True)
    hearing = serializers.SerializerMethodField()
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    created_by = serializers.StringRelatedField(default=serializers.CurrentUserDefault(), read_only=True)
    # company = companySerializer()
    # person = personsSerializer()
    # client_position = client_positionSerializer()
    # opponent = opponentSerializer()
    # opponent_position = opponent_positionSerializer()
    # assigned_team = assigned_teamSerializer()
    # Stage = stagesSerializer()

    def get_tasks(self,obj):
        if obj.id:
            case = get_object_or_404(LitigationCases,pk=obj.id)
            result = case.tasks.all().filter(is_deleted=False).values()
            return result

    # def get_paths(self,obj):
    #     if obj.id:
    #         case = get_object_or_404(LitigationCases,pk=obj.id)
    #         result = case.paths.all().filter(is_deleted=False).values()
    #         return result

    def get_hearing(self,obj):
        if obj.id:
            case = get_object_or_404(LitigationCases,pk=obj.id)
            result = case.hearing.all().filter(is_deleted=False).values()
            return result

    def get_documents(self,obj):
        if obj.id:
            case = get_object_or_404(LitigationCases,pk=obj.id)
            result = case.documents.all().filter(is_deleted=False).values()
            return result

    def get_comments(self,obj):
        if obj.id:
            case = get_object_or_404(LitigationCases,pk=obj.id)
            result = case.comments.all().filter(is_deleted=False).values()
            return result

            
    # def get_paths(self,obj):
    #     if obj.id:
    #         case = get_object_or_404(LitigationCases,pk=obj.id)
    #         result = case.paths.all().filter(is_deleted=False).values()
    #         return result

    class Meta:
        model = LitigationCases
#        list_serializer_class = FilteredListSerializer
        fields = [ 'id', 'name','description','case_category','priority','shared_with','court','ImportantDevelopment','case_type','case_status','judge','detective','client_position','opponent_position','assignee','Stage','internal_ref_number','comments','tasks','documents','paths','hearing','start_time','end_time','created_by','created_at']
        http_method_names = ['get', 'post', 'head','put']

class FoldersSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    court = serializers.SlugRelatedField(slug_field='name',queryset=court.objects.all())
    priority = serializers.SlugRelatedField(slug_field='priority',queryset=priorities.objects.all())
    folder_type = serializers.SlugRelatedField(slug_field='type',queryset=case_type.objects.all())
    client_position = serializers.SlugRelatedField(slug_field='name',queryset=client_position.objects.all())
    opponent_position = serializers.SlugRelatedField(slug_field='position',queryset=opponent_position.objects.all())
    Stage = serializers.SlugRelatedField(slug_field='name',queryset=stages.objects.all())
    assignee = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all())
    comments = commentsSerializer(many=True,read_only=True)
    documents = documentsSerializer(many=True,read_only=True)
    paths = PathSerializer(many=True,read_only=True )
    hearing = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField('get_tasks')
    ImportantDevelopment = ImportantDevelopmentsSerializer(many=True,read_only=True)
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    # company = companySerializer()
    # person = personsSerializer()
    # client_position = client_positionSerializer()
    # opponent = opponentSerializer()
    # opponent_position = opponent_positionSerializer()
    # assigned_team = assigned_teamSerializer()
    # Stage = stagesSerializer()

    def get_tasks(self,obj):
        if obj.id:
            folder = get_object_or_404(Folder,pk=obj.id)
            result = folder.tasks.all().filter(is_deleted=False).values()
            return result

    def get_hearing(self,obj):
        if obj.id:
            folder = get_object_or_404(Folder,pk=obj.id)
            result = folder.hearing.all().filter(is_deleted=False).values()
            return result

    # def get_paths(self,obj):
    #     if obj.id:
    #         folder = get_object_or_404(Folder,pk=obj.id)
    #         result = folder.paths.all().filter(is_deleted=False).values()
    #         return result


    class Meta:
        model = Folder
#        list_serializer_class = FilteredListSerializer
        fields = [ 'id', 'name','description','folder_category','priority','shared_with','court','ImportantDevelopment','folder_type','folder_status','judge','detective','client_position','opponent_position','assignee','Stage','internal_ref_number','comments','tasks','documents','paths','hearing','start_time','end_time','created_by','created_at']
        http_method_names = ['get', 'post', 'head','put']

