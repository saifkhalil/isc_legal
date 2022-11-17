from core.models import priorities
from rest_framework import serializers,status
from rest_framework.response import Response
from drf_dynamic_fields import DynamicFieldsMixin
from .models import LitigationCases,stages,client_position,opponent_position,Group,case_type,court
from core.serializers import commentsSerializer,documentsSerializer
from accounts.models import User
from activities.serializers import hearingSerializer
# from core.serializers import FilteredListSerializer


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

class LitigationCasesSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    court = serializers.SlugRelatedField(slug_field='name',queryset=court.objects.all())
    priority = serializers.SlugRelatedField(slug_field='priority',queryset=priorities.objects.all())
    case_type = serializers.SlugRelatedField(slug_field='type',queryset=case_type.objects.all())
    client_position = serializers.SlugRelatedField(slug_field='name',queryset=client_position.objects.all())
    opponent_position = serializers.SlugRelatedField(slug_field='position',queryset=opponent_position.objects.all())
    Stage = serializers.SlugRelatedField(slug_field='name',queryset=stages.objects.all())
    assignee = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all())
    comments = commentsSerializer(many=True,read_only=True)
    documents = documentsSerializer(many=True,read_only=True)
    hearing = hearingSerializer(many=True,read_only=True)
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    # company = companySerializer()
    # person = personsSerializer()
    # client_position = client_positionSerializer()
    # opponent = opponentSerializer()
    # opponent_position = opponent_positionSerializer()
    # assigned_team = assigned_teamSerializer()
    # Stage = stagesSerializer()

    class Meta:
        model = LitigationCases
#        list_serializer_class = FilteredListSerializer
        fields = [ 'id', 'name','description','case_category','priority','shared_with','court','case_type','judge','detective','client_position','opponent_position','assignee','Stage','internal_ref_number','comments','documents','hearing','start_time','end_time','created_by','created_at']
        http_method_names = ['get', 'post', 'head','put']

