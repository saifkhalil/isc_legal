from accounts.models import User
from django.contrib.auth.models import Group
from rest_framework import serializers
from cases.models import Group
from core.models import comments,replies,priorities,contracts,documents
from drf_dynamic_fields import DynamicFieldsMixin


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
    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all())
    modified_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all())
    
    class Meta:
        # list_serializer_class = FilteredListSerializer
        model = replies
        fields = ['id', 'reply','comment_id','created_by','created_at','modified_by','modified_at']

class prioritiesSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = priorities
        fields = ['id', 'priority']

class contractsSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    attachment = serializers.FileField()
    class Meta:
        model = contracts
        # list_serializer_class = FilteredListSerializer
        fields = ['id', 'name','attachment']

class documentsSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    attachment = serializers.FileField()
    class Meta:
        model = documents
        # list_serializer_class = FilteredListSerializer
        fields = ['id', 'name','attachment','case_id']

class commentsSerializer(DynamicFieldsMixin,serializers.ModelSerializer):
    

    created_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all())
    modified_by = serializers.SlugRelatedField(slug_field='username',queryset=User.objects.all())
    replies = serializers.SerializerMethodField('get_replis')

    def get_replis(self, obj):
        # You can do more complex filtering stuff here.
        return repliesSerializer(obj.replies.filter(is_deleted=False), many=True, read_only=True).data



    class Meta:
        ref_name = 'Comments'
        # list_serializer_class = FilteredListSerializer
        model = comments
        fields = ['id', 'comment','replies','case_id','event_id','task_id','hearing_id','created_by','created_at','modified_by','modified_at']
