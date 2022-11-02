from audioop import reverse
from lib2to3.pgen2.tokenize import generate_tokens
from django.contrib import messages
from urllib import request
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from rest_framework.authtoken.models import Token
from django.contrib.sites.shortcuts import get_current_site
from accounts.forms import RegistrationForm, UserAuthenticationForm, UserUpdateForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from accounts.models import User
from django.utils.translation import gettext_lazy as _




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
                'firstname'), form.cleaned_data.get('lastname'))
            phone = str(form.cleaned_data.get('phone'))[1:]
            send_active_email(user, request)
            #account = authenticate(request, email=email, password=raw_password)
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


def logout_view(request):
    logout(request)
    return redirect('home')


def login_view(request):
    context = {}
    if request.GET.get('next') is None:
        next_page = 'home'
    else:
        next_page = request.GET.get('next')
    user = request.user
    if user.is_authenticated:
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
                                     _('It looks like your account has been blocked Please contact system admin for more information.'))
                return render(request, "account/login.html", context)
            if user:
                login(request, user)
                return redirect(next_page)
    else:
        form = UserAuthenticationForm()
    context['login_form'] = form
    return render(request, "account/login.html", context)


def account_view(request):
    context = {}
    if request.POST:
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.initial = {
                "email": request.POST['email'],
                "username": request.POST['username'],
                "firstname": request.POST['firstname'],
                "lastname": request.POST['lastname'],
                "phone": request.POST['phone'],
            }
            form.save()
            context['success_message'] = _("Profile Updated")
    else:
        form = UserUpdateForm(

            initial={
                "email": request.user.email,
                "username": request.user.username,
                "firstname": request.user.firstname,
                "lastname": request.user.lastname,
                "phone": request.user.phone,
            }
        )
    context['account_form'] = form
    return render(request, "account/account.html", context)


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
