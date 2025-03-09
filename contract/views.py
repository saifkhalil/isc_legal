from django.shortcuts import render
from django_celery_beat.models import ClockedSchedule, PeriodicTask
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import timedelta, datetime
from core.models import Notification
from .models import Contract, Type, Payment, Duration
from .serializers import ContractSerializer, PaymentSerializer, DurationSerializer, TypeSerializer
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from core.classes import StandardResultsSetPagination
from rest_framework import permissions
from cases.permissions import Manager_SuperUser, MyPermission
from accounts.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from rest_framework.response import Response
from rest_framework.decorators import action
from core.classes import dict_item, GetUniqueDictionaries
import json
from django.db.models import Q


class ContractViewSet(viewsets.ModelViewSet):
    model = Contract
    queryset = Contract.objects.all().order_by('-created_by')
    serializer_class = ContractSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticated,
        Manager_SuperUser
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]
    filterset_fields = ['id', 'name', 'description', 'type',
                        'company', 'out_side_iraq', 'start_time', 'end_time', 'auto_renewal', 'assignee']
    search_fields = ['@name', '@description', '=id']
    ordering_fields = ['created_at', 'id', 'modified_at']
    ordering = ['-id']

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification_users: list = []
        req_name = request.data.get('name') if request.data.get('name') not in ('', None) else None
        req_payments = request.data.get('payments') if request.data.get('payments') not in ('', None) else None
        req_description = request.data.get('description') if request.data.get('description') not in ('', None) else None
        req_type = Type.objects.get(name=request.data.get('type')) if request.data.get('type') else None
        req_company = request.data.get('company') if request.data.get('company') not in ('', None) else None
        req_out_side_iraq = request.data.get('out_side_iraq') if request.data.get('out_side_iraq') not in ('', None) else None
        req_total_amount = request.data.get('total_amount') if request.data.get('total_amount') not in ('', None) else None
        req_start_time = request.data.get('start_time') if request.data.get('start_time') not in ('', None) else None
        req_end_time = request.data.get('end_time') if request.data.get('end_time') not in ('', None) else None
        req_first_party = request.data.get('first_party') if request.data.get('first_party') not in ('', None) else None
        req_second_party = request.data.get('second_party') if request.data.get('second_party') not in ('', None) else None
        req_third_party = request.data.get('third_party') if request.data.get('third_party') not in ('', None) else None
        req_auto_renewal = request.data.get('auto_renewal') if request.data.get('auto_renewal') not in ('', None) else None
        req_penal_clause = request.data.get('penal_clause') if request.data.get('penal_clause') not in ('', None) else None
        req_assignee = User.objects.get(username=request.data.get('assignee')) if request.data.get('assignee') not in ('', None) else None
        req_created_by = User.objects.get(username=request.data.get('created_by')) if request.data.get('created_by') not in ('', None) else None
        req_created_at = request.data.get('created_at') if request.data.get('created_at') not in ('', None) else timezone.now()
        contract = Contract(
            id=None,
            name=req_name,
            description=req_description,
            type=req_type,
            company=req_company,
            out_side_iraq=req_out_side_iraq,
            total_amount=req_total_amount,
            first_party=req_first_party,
            second_party=req_second_party,
            # third_party=req_third_party,
            auto_renewal=req_auto_renewal,
            penal_clause=req_penal_clause,
            assignee=req_assignee,
            start_time=req_start_time,
            end_time=req_end_time,
            created_by=req_created_by,
            created_at=req_created_at
        )
        contract.save()
        if req_payments:
            for payment_data in req_payments:
                duration_type = str(payment_data.get('duration'))
                print('duration type', duration_type)
                payment_date = datetime.strptime(payment_data.get('date'), '%Y-%m-%dT%H:%M:%S.%fZ')
                Payment.objects.create(contract=contract, duration=Duration.objects.get(type=duration_type), amount=payment_data.get('amount'), date=payment_date)
        notification_users.append(contract.assignee)
        if request.data.get('shared_with'):
            shared_with_list: list = list(request.data.get('shared_with'))
            shared_with_users: list = []
            for sh in shared_with_list:
                contract.shared_with.add(sh)
                shu = User.objects.get(id=sh)
                shared_with_users.append(shu)
            contract.shared_with.add(request.user)
            notification_users.extend(shared_with_users)
        else:
            contract.shared_with.add(request.user)
        managers_notifications = User.objects.filter(
            is_manager=True, email_notification=True)
        managers_users = [manager for manager in managers_notifications]
        notification_users.extend(managers_users)
        notification_users_set = set(notification_users)
        if request.user in notification_users_set:
            notification_users_set.remove(request.user)
        for notification_user in notification_users_set:
            Notification.objects.create_notification(action='create',
                                                     content_type=ContentType.objects.get_for_model(contract),
                                                     object_id=contract.id, action_by=request.user, user=notification_user,
                                                     object_name=contract.name,
                                                     role='manager')
        execution_time = contract.created_at + timedelta(days=30)
        # schedule, created = ClockedSchedule.objects.get_or_create(clocked_time=execution_time)
        # PeriodicTask.objects.create(clocked=schedule,
        #                             one_off=True,
        #                             name=f'{contract.name} {contract.created_at}',
        #                             task='cases.tasks.late_case',
        #                             args=json.dumps([contract.id, contract.created_by.id]),
        #                             )
        serializer = self.get_serializer(contract)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):

        contract = Contract.objects.filter(id=pk)
        contracts = Contract.objects.get(id=pk)
        if contracts.is_deleted:
            return Response(data={"detail": "العقد غير موجود"}, status=status.HTTP_404_NOT_FOUND)
        notification_users: list = []
        managers_notifications = User.objects.filter(
            is_manager=True, email_notification=True)
        managers_users = [manager for manager in managers_notifications]
        shared_with_users = [shared_with for shared_with in contracts.shared_with.all()]
        notification_users.extend(managers_users)
        notification_users.extend(shared_with_users)
        notification_users_set = set(notification_users)
        if request.user in notification_users_set:
            notification_users_set.remove(request.user)
        for notification_user in notification_users_set:
            Notification.objects.create_notification(action='delete',
                                                     content_type=ContentType.objects.get_for_model(contracts),
                                                     object_id=contracts.id, object_name=contracts.name, action_by=request.user,
                                                     user=notification_user,
                                                     role='manager')
        contracts.paths.all().delete()
        contract.update(is_deleted=True, modified_by=request.user,
                    modified_at=timezone.now())

        return Response(data={"detail": "تم مسح العقد بنجاح"}, status=status.HTTP_200_OK)

    def get_queryset(self):
        version = self.request.version
        print('version: ', version)
        start_time = self.request.query_params.get('start_time', None)
        queryset = Contract.objects.all().order_by(
            '-created_by').filter(is_deleted=False)
        current_user_id = self.request.user.id
        cuser = User.objects.get(id=current_user_id)
        is_manager = cuser.is_manager
        is_superuser = cuser.is_superuser
        is_contract_manager = cuser.is_contract_manager

        if start_time not in ('', None):
            req_date = datetime.strptime(start_time, '%Y-%m-%d').date()
            queryset = queryset.filter(start_time__year=req_date.year, start_time__month=req_date.month,
                                       start_time__day=req_date.day)
        if is_manager or is_superuser or is_contract_manager:
            queryset = queryset
        else:
            filter_query = Q(shared_with__id__exact=current_user_id) | Q(created_by__id__exact=current_user_id) | Q(
                assignee__id__exact=current_user_id)
            queryset = queryset.filter(filter_query).distinct()
        return queryset

    def perform_update(self, serializer):
        instance = self.get_object()
        serializer.save(modified_by=self.request.user)

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def related_objects(self, request):
        contracts = self.get_queryset()
        type: list = []
        payments: list = []
        assignees: list = []
        for contract in contracts:
            if contract.type:
                type.append(dict_item(contract.type.id, contract.type.name))
            if contract.payments:
                payments.append(dict_item(contract.payments.id, contract.payments.amount))
            if contract.assignee:
                assignees.append(dict_item(contract.assignee.id, contract.assignee.username))

        type_set = GetUniqueDictionaries(type)
        payments_set = GetUniqueDictionaries(payments)
        assignees_set = GetUniqueDictionaries(assignees)
        return Response(status=status.HTTP_200_OK,
                        data={'Type': type_set, 'payments': payments_set, 'assignees': assignees_set})


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-id')
    serializer_class = PaymentSerializer
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "contract.Payment"

    def perform_create(self, serializer):
        # Set the user who is creating the payment
        serializer.save(created_by=self.request.user)

class DurationViewSet(viewsets.ModelViewSet):
    queryset = Duration.objects.all().order_by('-id')
    serializer_class = DurationSerializer
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "contract.Duration"


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all().order_by('-id')
    serializer_class = TypeSerializer
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [permissions.IsAuthenticated, MyPermission]
    perm_slug = "contract.Type"
