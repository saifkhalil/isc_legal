from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from accounts.models import User
from cases.serializers import ImportantDevelopmentsSerializer
from core.serializers import commentsSerializer, PathSerializer
from .models import Contract, Payment, Duration, Type


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ['id', 'name']


class DurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Duration
        fields = ['id', 'type', 'no_of_days', 'reminder_days', 'is_recurring']


class PaymentSerializer(serializers.ModelSerializer):
    duration = serializers.SlugRelatedField(
        slug_field='type', queryset=Duration.objects.all())

    # def get_duration(self, obj):
    #     return DurationSerializer(obj.duration.filter(is_deleted=False), many=True, read_only=True).data

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'date', 'duration', 'contract']


class PaymentSerializerInContract(serializers.ModelSerializer):
    duration = serializers.SlugRelatedField(
        slug_field='type', queryset=Duration.objects.all())

    # def get_duration(self, obj):
    #     return DurationSerializer(obj.duration.filter(is_deleted=False), many=True, read_only=True).data

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'date', 'duration']

class ContractSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    name = serializers.CharField(required=True, read_only=False)
    description = serializers.CharField(required=True, read_only=False)
    type = serializers.SlugRelatedField(
        slug_field='name', queryset=Type.objects.all())
    company = serializers.CharField(required=True, read_only=False)
    out_side_iraq = serializers.BooleanField()
    total_amount = serializers.IntegerField()
    payments = PaymentSerializerInContract(many=True)
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False)
    first_party = serializers.CharField(required=True, read_only=False)
    second_party = serializers.CharField(required=True, read_only=False)
    # third_party = serializers.CharField(required=False)
    auto_renewal = serializers.BooleanField()
    penal_clause = serializers.CharField(required=False, read_only=False)
    paths = PathSerializer(many=True, read_only=True)
    assignee = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all())
    shared_with = serializers.SlugRelatedField(
        slug_field='id', many=True, queryset=User.objects.all())
    ImportantDevelopment = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField('get_comments')

    created_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                              slug_field='username', read_only=True)
    modified_by = serializers.SlugRelatedField(default=serializers.CurrentUserDefault(),
                                               slug_field='username', read_only=True)

    def get_payments(self, obj):
        return PaymentSerializer(obj.payments.filter(is_deleted=False), many=True, read_only=True).data

    def get_comments(self, obj):
        return commentsSerializer(obj.comments.filter(is_deleted=False), many=True, read_only=True).data

    def get_ImportantDevelopment(self, obj):
        return ImportantDevelopmentsSerializer(obj.ImportantDevelopment.filter(is_deleted=False), many=True, read_only=True).data

    class Meta:
        model = Contract
        fields = ['id', 'name', 'description', 'type', 'out_side_iraq', 'total_amount', 'payments', 'company',
                  'shared_with',  'ImportantDevelopment', 'assignee', 'comments', 'first_party', 'second_party',
                  'third_party', 'auto_renewal', 'penal_clause', 'paths', 'start_time', 'end_time', 'created_by',
                  'created_at', 'modified_by', 'modified_at']
        http_method_names = ['get', 'post', 'head', 'put']

