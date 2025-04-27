from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from accounts.models import Employees


class EmployeesSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Employees
        fields = ['full_name', 'email', ]
        http_method_names = ['get', 'head','post']


class EmpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employees
        fields = '__all__'
