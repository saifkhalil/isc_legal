from .models import LitigationCases
from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from .models import LitigationCases,stages,client_position,opponent_position,Group,case_type,court
from core.serializers import commentsSerializer,documentsSerializer

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

    comments = commentsSerializer(many=True,required=False, allow_null=True)
    documents = documentsSerializer(many=True,required=False, allow_null=True)
    # company = companySerializer()
    # person = personsSerializer()
    # client_position = client_positionSerializer()
    # opponent = opponentSerializer()
    # opponent_position = opponent_positionSerializer()
    # assigned_team = assigned_teamSerializer()
    # Stage = stagesSerializer()
    class Meta:
        model = LitigationCases
        fields = [ 'id', 'name','description','case_category','priority','shared_with','court','case_type','judge','detective','client_position','opponent_position','assignee','Stage','internal_ref_number','comments','documents','start_time','end_time']
        http_method_names = ['get', 'post', 'head','put']

