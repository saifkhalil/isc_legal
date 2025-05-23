import six
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import FormView
from django_filters import rest_framework as filters
from elasticsearch.exceptions import ElasticsearchException
from haystack.query import SearchQuerySet
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.forms import UserAuthenticationForm,UserUpdateForm
from accounts.models import User, Employees
from accounts.serializers import EmployeesSerializer, EmpSerializer
from activities.models import task_categories, task, hearing
from cases.models import LitigationCases
from contract.models import Contract


def get_user_queryset(user=None):
    if user and (user.is_superuser or user.is_staff):
        queryset = get_user_model().objects.all()
    else:
        queryset = get_user_model().objects.filter(
            is_superuser=False, is_staff=False
        )

    return queryset.order_by('username')

def login_view(request):
    context = {}
    if request.GET.get('next') is None:
        next_page = 'home'
    else:
        next_page = request.GET.get('next')
    user = request.user
    if user.is_authenticated:
        request.session['django_language'] = user.language  # Store language in session
        activate(user.language)
        return redirect('home')
    if request.POST:
        form = UserAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)

            if not user.is_verified:
                messages.add_message(request, messages.ERROR,
                                     _('Email is not verified, please check your email inbox'))
                return render(request, "account/login.html", context)
            if user.is_blocked:
                messages.add_message(request, messages.ERROR,
                                     _('It looks like your account has been blocked Please contact saif.ibrahim@qi.iq for more information.'))
                return render(request, "account/login.html", context)
            if user:
                login(request, user)
                request.session['django_language'] = user.language  # Store language in session
                print(f'{user.language=}')
                activate(user.language)  # Set active language
                return redirect(next_page)
    else:
        form = UserAuthenticationForm()
    context['login_form'] = form
    return render(request, "account/login.html", context)

def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')



class UserSetPasswordView(FormView):
    form_class = SetPasswordForm
    template_name = "registration/password_reset_confirm.html"
    pk_url_kwarg = 'user_id'
    source_queryset = get_user_queryset()
    success_message = 'Password change request performed on %(count)d user'
    success_message_plural = 'Password change request performed on %(count)d users'

    def get_extra_context(self):
        queryset = self.object_list

        result = {
            'title': ngettext(
                singular='Change user password',
                plural='Change users passwords',
                number=queryset.count()
            )
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        'Change password for user: %s'
                    ) % queryset.first()
                }
            )

        return result

    def get_form_extra_kwargs(self):
        queryset = self.object_list
        result = {}
        if queryset:
            result['user'] = queryset.first()
            return result
        else:
            raise PermissionDenied

    def object_action(self, form, instance):
        try:
            instance.set_password(
                raw_password=form.cleaned_data['new_password1']
            )
            instance.save()
            messages.success(
                message=_(
                    'Successful password reset for user: %s.'
                ) % instance, request=self.request
            )
        except Exception as exception:
            messages.error(
                message=_(
                    'Error reseting password for user "%(user)s": %(error)s'
                ) % {
                            'error': exception, 'user': instance
                        }, request=self.request
            )


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                six.text_type(user.pk) + six.text_type(timestamp) +
                six.text_type(user.is_active)
        )


account_activation_token = TokenGenerator()


def send_active_email(user, request):
    current_site = request.get_host()
    message = 'text version of HTML message'
    email_subject = 'Activate your account'
    email_body = render_to_string('account/verification.html', {
        'user': user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user)
    })

    send_mail(email_subject, message, settings.DEFAULT_FROM_EMAIL, [
        user.email], fail_silently=True, html_message=email_body)


def send_active(request, userid):
    user = User.objects.get(id=userid)
    message = 'text version of HTML message'
    email_subject = 'Activate your account'
    email_body = render_to_string('account/verification.html', {
        'user': user,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user)
    })

    send_mail(email_subject, message, settings.DEFAULT_FROM_EMAIL, [
        user.email], fail_silently=True, html_message=email_body)
    return redirect('dashboard')


def registration_view(request):
    context = {}
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.is_verified = False
            user.save()
            email = form.cleaned_data.get('email')
            # async_send_mail = sync_to_async(send_mail)
            # asyncio.create_task(async_send_mail('Celery Task Worked!2','This is proof the task worked!', 'saif780@gmail.com', ['saif780@gmail.com']))

            raw_password = form.cleaned_data.get('password1')
            fullname = "%s %s" % (form.cleaned_data.get(
                'first_name'), form.cleaned_data.get('lastname'))
            phone = str(form.cleaned_data.get('phone'))[1:]
            send_active_email(user, request)
            # account = authenticate(request, email=email, password=raw_password)
            # if account:
            #    login(request, account)
            messages.add_message(request, messages.SUCCESS,
                                 _('User registered successfully, verification email has been sent, please check it '))
            return redirect('login')
        else:
            context['form'] = form
    else:
        if not request.user.is_authenticated:
            form = RegistrationForm()
            context['form'] = form
        else:
            return render(request, 'after_register.html')
    return render(request, 'account/register.html', context)


def calculate_status_counts(queryset, status_field):
    total = queryset.count()
    done = queryset.filter(**{f"{status_field}__is_done": True}).count()
    new = queryset.filter(**{f"{status_field}__status": "New"}).count()
    progress = total - (done + new)

    def percent(part):
        return int((part / total) * 100) if total > 0 else 0

    return {
        "count_all": total,
        "count_done": done,
        "count_new": new,
        "count_progress": progress,
        "count_done_per": percent(done),
        "count_new_per": percent(new),
        "count_progress_per": percent(progress),
    }


def account_view(request):
    user = request.user

    cases_data = calculate_status_counts(LitigationCases.objects.filter(created_by=user), "case_status")
    tasks_data = calculate_status_counts(task.objects.filter(created_by=user), "task_status")
    hearings_data = calculate_status_counts(hearing.objects.filter(created_by=user), "hearing_status")

    context = {
        "cases": cases_data,
        "tasks": tasks_data,
        "hearings": hearings_data,
    }

    return render(request, "user_profile.html", context)


def must_authenticate_view(request):
    return render(request, 'account/must_authenticate.html', {})


def active_user(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_verified = True
        user.save()

        messages.add_message(request, messages.SUCCESS,
                             _('Email Verified, you can now login'))
        return redirect('login')
    messages.add_message(request, messages.ERROR,
                         _('Email Verification erorr, please try agin'))
    return redirect('login')


def block_user(request, userid):
    selected_user = User.objects.get(id=userid)
    selected_user.is_blocked = True
    selected_user.save()
    return redirect('dashboard')


def unblock_user(request, userid):
    selected_user = User.objects.get(id=userid)
    selected_user.is_blocked = False
    selected_user.save()
    return redirect('dashboard')


class Top10Pagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 10


class EmployeesFilter(filters.FilterSet):
    full_name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Employees
        fields = ['full_name', ]


class EmployeesViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = Top10Pagination
    queryset = Employees.objects.all()
    serializer_class = EmployeesSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = EmployeesFilter

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(60 * 60))
    def dispatch(self, *args, **kwargs):
        return super(EmployeesViewSet, self).dispatch(*args, **kwargs)


class SearchEmployeesAPIView(viewsets.ModelViewSet):
    queryset = Employees.objects.all()  # Set your queryset here
    serializer_class = EmpSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        search_results = SearchQuerySet().filter(text=query)

        if not search_results:
            suggestions = self.get_suggestions(query)
            return Response({"suggestions": suggestions})

        serialized_results = [result.object for result in search_results]
        return Response(serialized_results)

    def get_suggestions(self, query):
        try:
            # Use Elasticsearch's suggest API for "did you mean" suggestions
            suggestions = SearchQuerySet().spelling_suggestion(query)
            return [suggestion for suggestion in suggestions]
        except ElasticsearchException:
            return []  # Return an empty list if suggestions cannot be generated


class SearchEmployeeAPIView(APIView):
    queryset = Employees.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get(self, request, format=None):
        query = request.query_params.get('q', '')
        search_results_contains = SearchQuerySet().filter(text__contains=query)
        search_results_contains_highlight = SearchQuerySet().filter(text__contains=query).highlight(
    pre_tags=['<strong>'], post_tags=['</strong>'])
        search_results_fuzzy = SearchQuerySet().filter(text__fuzzy=query)

        # if not search_results:
        #     suggestions = self.get_suggestions(query)
        #
        #     if suggestions is not None:  # Check if suggestions were generated
        #         return Response({"results": [], "suggestions": suggestions})

        serialized_results_contains = [self.serialize_employee(result.object) for result in search_results_contains]
        serialized_results_contains_highlight = [{"full_name": result.highlighted[0], 'email': result.email} for result in search_results_contains_highlight]
        serialized_results_fuzzy = [self.serialize_employee(result.object) for result in search_results_fuzzy]

        return Response(
            data={
            # "results": serialized_results_contains,
            "results": serialized_results_contains_highlight,
            "suggestions": serialized_results_fuzzy
        }
        )

    def serialize_employee(self, employee):
        # Use your EmployeesSerializer to serialize the employee object
        serializer = EmployeesSerializer(employee)
        return serializer.data

    def get_suggestions(self, query):
        try:
            suggestions = SearchQuerySet().spelling_suggestion(query)
            if suggestions:
                return suggestions
            else:
                return []
        except ElasticsearchException:
            return []
