"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from rest_framework import routers
from accounts.views import (
    registration_view,
    account_view,
    active_user,
    must_authenticate_view,
    send_active,
    block_user,
    unblock_user,
    UserSetPasswordView,
    EmployeesViewSet,
    SearchEmployeesAPIView,
    SearchEmployeeAPIView,
    login_view,
    logout_view
)
from django.views.decorators.cache import cache_page
router = routers.DefaultRouter()
router.register(r'employees', EmployeesViewSet, "employees")

urlpatterns = [
    # path('after', views.after, name='after'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify/<uuid:userid>', send_active, name="send_active"),
    path('block_user/<uuid:userid>', block_user, name="block_user"),
    path('unblock_user/<uuid:userid>', unblock_user, name="unblock_user"),
    path('register/', registration_view, name="register"),
    path('profile/', login_required(account_view), name="account"),
    path('activate_user/<uidb64>/<token>', active_user, name='active'),
    path('<int:user_id>/set_password/',name='user_set_password', view=UserSetPasswordView.as_view()),
    path('must_authenticate/', must_authenticate_view, name="must_authenticate"),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'), name='password_change_done'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html'), name='password_change'),
    path('password_reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password_reset/', auth_views.PasswordResetView.as_view(html_email_template_name='registration/html_password_reset_email.html'),
         name='password_reset'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('', include(router.urls)),
    path('searchs/', SearchEmployeesAPIView.as_view({'get': 'list'}), name='search-employees'),


]
