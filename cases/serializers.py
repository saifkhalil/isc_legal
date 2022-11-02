from .models import LitigationCases
from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from core.models import replies,comments
from .models import LitigationCases,practice_area,company,stages,persons,client_position,opponent_position,Group
from core.serializers import commentsSerializer

class practice_areaSerializer(serializers.ModelSerializer):
    class Meta:
        model = practice_area
        fields = ['id', 'name']

class companySerializer(serializers.ModelSerializer):
    class Meta:
        model = company
        fields = ['id', 'full_name','name','foreign_name','category_id','sub_category_id','company_legal_type_id','company_group_id','reference']

class personsSerializer(serializers.ModelSerializer):
    class Meta:
        model = persons
        fields = ['id', 'name']


class client_positionSerializer(serializers.ModelSerializer):
    class Meta:
        model = client_position
        fields = ['id', 'name']

class opponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = client_position
        fields = ['id', 'name']


class opponent_positionSerializer(serializers.ModelSerializer):
    class Meta:
        model = opponent_position
        fields = ['id', 'position']

class assigned_teamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class stagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = stages
        fields = ['id', 'name']

class LitigationCasesSerializer(DynamicFieldsMixin,serializers.ModelSerializer):

    comments = commentsSerializer(many=True)
    company = companySerializer()
    person = personsSerializer()
    client_position = client_positionSerializer()
    opponent = opponentSerializer()
    opponent_position = opponent_positionSerializer()
    assigned_team = assigned_teamSerializer()
    Stage = stagesSerializer()
    class Meta:
        model = LitigationCases
        fields = [ 'id', 'cid', 'name','description','case_category','practice_area','arrival_date','company','person','opponent','client_position','opponent','opponent_position','assigned_team','Stage','internal_ref_number','comments']
        http_method_names = ['get', 'post', 'head','put']

