from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
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
from django.core.cache import cache
from urllib.parse import urlencode

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


@login_required
def contracts_list(request):
    number_of_records = 10
    keywords = type = assignee = out_side_iraq = auto_renewal = company = None
    type_set = assignee_set = company_set =  None

    if request.method == 'GET':
        # Clear filters and redirect if needed.
        if request.GET.get('clear'):
            for key in ['keywords', 'type', 'assignee', 'out_side_iraq', 'auto_renewal', 'company', 'number_of_records']:
                request.session.pop(key, None)
            return redirect(request.path)

        # Retrieve filter parameters from GET or session.
        if 'keywords' in request.GET:
            keywords = request.GET.get('keywords')
            request.session['keywords'] = keywords  # Update session even if empty
        else:
            keywords = request.session.get('keywords', '')
        type = request.GET.get('type') or request.session.get('type',0)
        assignee = request.GET.get('assignee') or request.session.get('assignee',0)
        out_side_iraq = request.GET.get('out_side_iraq') or request.session.get('out_side_iraq',0)
        auto_renewal = request.GET.get('auto_renewal') or request.session.get('auto_renewal',0)
        company = request.GET.get('company') or request.session.get('company',0)

        # Save parameters to session if provided.
        for key, value in (('keywords', keywords), ('type', type),
                           ('assignee', assignee), ('out_side_iraq', out_side_iraq),
                           ('auto_renewal', auto_renewal), ('company', company)):
            if value is not None:
                request.session[key] = value

        # Handle number_of_records.
        if request.GET.get('number_of_records'):
            try:
                number_of_records = int(request.GET.get('number_of_records'))
            except ValueError:
                number_of_records = 10
            request.session['number_of_records'] = number_of_records
        else:
            number_of_records = request.session.get('number_of_records', 10)

        # Build search query using Q objects.
        query = Q()
        if keywords:
            query |= Q(name__icontains=keywords)
            # Filter out words shorter than 2 characters.
            # query_words = [w for w in keywords.split() if len(w) >= 2]
            # for word in query_words:
            #     query |= Q(description__icontains=word)
        if type and type != '0':
            query &= Q(type=type)
        if assignee and assignee != '0':
            query &= Q(assignee__id=assignee)
        if out_side_iraq and out_side_iraq != '0':
            if out_side_iraq == 'International':
                qy_out_side_iraq = True
            elif out_side_iraq == 'Domestic':
                qy_out_side_iraq = False
            query &= Q(out_side_iraq=qy_out_side_iraq)
        # Optionally, add status filtering if needed:
        if auto_renewal and auto_renewal != '0':
            query &= Q(auto_renewal=auto_renewal)
        if company and company != '0':
            query &= Q(company=company)

        # Get base queryset.
        contracts_qs = Contract.objects.filter(is_deleted=False).order_by('-created_by')

        # Retrieve filter dropdown data from cache or compute if not cached.
        contract_key = "contracts_objects"
        cached_data = cache.get(contract_key)
        if cached_data:
            types_set = cached_data.get('types')
            assignees_set = cached_data.get('assignees')
            companies_set = cached_data.get('companies')
        else:
            types = []
            assignees = []
            companies = []
            for contract in contracts_qs:
                if contract.type:
                    types.append(dict_item(contract.type.id, contract.type.name))
                if contract.assignee:
                    assignees.append(dict_item(contract.assignee.id, contract.assignee.username))
                if contract.company:

                    companies.append(dict_item(contract.company, contract.company))
            assignees_set = GetUniqueDictionaries(assignees)
            types_set = GetUniqueDictionaries(types)
            companies_set = GetUniqueDictionaries(companies)
            cached_data = {
                'types': types_set,
                'assignees': assignees_set,
                'companies': companies_set,
            }
            cache.set(contract_key, cached_data, timeout=None)

        # Apply filters.
        hearings_qs = contracts_qs.filter(query)
    else:
        hearings_qs = Contract.objects.filter(is_deleted=False).order_by('-created_by')

    # Set up pagination.
    paginator = Paginator(hearings_qs, number_of_records)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=2, on_ends=2)

    # Prepare session info for the template.
    session_info = {
        'number_of_records': number_of_records or 10,
        'keywords': keywords or '',
        'type': type or 0,
        'assignee': assignee or 0,
        'out_side_iraq': out_side_iraq or 0,
        'auto_renewal': auto_renewal or 0,
        'company': company or 0,
    }

    # Build a filter query string to be used in pagination links.
    # Only include filter keys (exclude 'page').
    filter_params = {}
    for key in ['keywords', 'type', 'assignee', 'out_side_iraq', 'auto_renewal', 'company', 'number_of_records']:
        value = request.session.get(key)
        if value:
            filter_params[key] = value
    filter_query = urlencode(filter_params)
    context = {
        'contracts': page_obj,
        'assignees': assignees_set,
        'types': types_set,
        'companies': companies_set,
        'page_range': page_range,
        'session': json.dumps(session_info),
        'filter_query': filter_query,  # New variable for pagination links.
    }
    return render(request, 'contracts/contracts_list.html', context)


@require_POST
def delete_contract(request, pk=None):
    print('delete_contract',pk)
    instance = Contract.objects.get(pk=pk)
    if not (request.user.is_manager or request.user.is_superuser):
        return JsonResponse({'success': False, 'message':"You do not have permission to perform this action."},status=401)
    instance = get_object_or_404(Contract, pk=pk)
    instance.is_deleted = True
    instance.modified = timezone.now()
    # Assuming you have a field to record the modifying user:
    instance.modified_by = request.user
    instance.save()
    return JsonResponse({'success': True, 'message': 'Contract has been deleted successfully.'},status=200)