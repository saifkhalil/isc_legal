"""isc_legal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from accounts.views import SearchEmployeeAPIView, account_view
from activities.forms import TaskForm, HearingForm, ContactForm1, ContactForm2
from activities.views import tasks_list, delete_task, hearings_list, delete_hearing, task_view, hearing_view, \
    new_hearing_comment, new_task_comment, new_task_path
from cases.views import cases_list, delete_case, notations_list, delete_notation, AdministrativeInvestigations_list, \
    delete_AdministrativeInvestigation, case_view, get_stages_for_case_type, new_case_path, \
    new_case_ImportantDevelopment, new_case_comment, notation_view, new_notation_comment, new_notation_path, \
    new_notation_ImportantDevelopment, AdministrativeInvestigations_view, new_AdministrativeInvestigation_path, \
    new_AdministrativeInvestigation_ImportantDevelopment
from contract.views import contracts_list, delete_contract, create_contract_with_payments, contract_view, \
    new_contract_ImportantDevelopment, new_contract_comment
from . import views
from .consumers import NotificationConsumer
from .views import (
    APIPathListView, APIPathView, myhome, about, load_more_notifications, read_all_notifications, read_notification,
    delete_all_notifications, delete_notification, new_path_docs, new_case_comment_reply,
    new_comment_reply, delete_path, Paths_list, doc_images, open_document
)
from activities.views import ContactWizard,show_message_form_condition


def handler404(request, *args, **argv):
    response = render(request, '404.html')
    response.status_code = 404
    return response


def handler500(request, *args, **argv):
    response = render(request, '500.html')
    response.status_code = 500
    return response

def trigger_error(request):
        division_by_zero = 1 / 0


from patches import routers

router = routers.DefaultRouter()
router.register(r'groups', views.GroupViewSet, basename='Groups')
router.register(r'comments', views.commentsViewSet, basename='comments')
# router.register(r'directory', views.directoriesViewSet,basename='directory')
router.register(r'replies', views.repliesViewSet, basename='replies')
router.register(r'priorities', views.prioritiesViewSet, basename='priorities')
router.register(r'contracts', views.contractsViewSet, basename='contracts')
router.register(r'documents', views.documentsViewSet, basename='documents')
router.register(r'events', views.eventsViewSet, basename='events')
router.register(r'cases_events', views.caseseventsViewSet, basename='cases_events')
router.register(r'status', views.StatusViewSet, basename='status')
router.register(r'notification', views.NotificationViewSet, basename='notification')
router.register(r'log', views.LogsViewSet, basename='log')

urlpatterns = [
                  path('admin/doc/', include('django.contrib.admindocs.urls')),
                  path('api/', include(router.urls), name='home'),
                  path('api/accounts/', include('accounts.urls'), name='accounts'),
                  path('api/cases/', include('cases.urls'), name='cases'),
                  path('api/activities/', include('activities.urls'), name='activities'),
                  path('api/contract/', include('contract.urls'), name='contract'),
                  path('api/auth/', include('djoser.urls')),
                  path('api/auth/', include('djoser.urls.authtoken')),
                  path('api/jwt/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('api/jwt/verify/', TokenVerifyView.as_view(), name='token_verify'),
                  path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
                  path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
                  path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
                  path('api/paths/', name='path-list', view=APIPathListView.as_view()),
                  path('api/paths/<path_id>/', name='path-detail', view=APIPathView.as_view()),
                  path('api/pathchildren/<int:pk>/', views.SelectedPathChildren.as_view(),
                       name='selected-object-children'),
                  path('api/accounts/search/', SearchEmployeeAPIView.as_view(), name='search-employees'),
                  

              ]
urlpatterns += i18n_patterns(
    path('i18n/', include('django.conf.urls.i18n')),
    path('set-language/',views.set_language, name='set_language'),
    path('set-theme-color/',views.set_theme_color, name='set_theme_color'),
    path('set-animation/',views.set_animation, name='set_animation'),
    path('is-grid/',views.set_grid_view, name='set_grid_view'),
    path("select2/", include("django_select2.urls")),
    path('',myhome,name='home'),
    path('myprofile/',login_required(account_view),name='my_profile'),
    path('cases/',login_required(cases_list),name='cases_list'),
    path('cases/create/', login_required(case_view), {'mode': 'create'}, name='case_create'),
    path("get-stages/", get_stages_for_case_type, name="get_stages"),
    path('cases/<int:pk>/',login_required(delete_case),name='delete_case'),
    path('cases/<int:case_id>/edit/', login_required(case_view), {'mode': 'edit'}, name='case_edit'),
    path('cases/<int:case_id>/view/', login_required(case_view), {'mode': 'view'}, name='case_view'),
    path('cases/<int:case_id>/new_path/', login_required(new_case_path), name='new_case_path'),
    path('cases/<int:case_id>/new_id/', login_required(new_case_ImportantDevelopment), name='new_case_ImportantDevelopment'),
    path('cases/<int:case_id>/new_comment/', login_required(new_case_comment), name='new_case_comment'),
    path('cases/<int:case_id>/comments/<int:comment_id>/new_reply', login_required(new_case_comment_reply), name='new_case_comment_reply'),
    path('notations/', notations_list, name='notations_list'),
    path('notations/<int:pk>/', login_required(delete_notation), name='delete_notation'),
    path('notations/create/', login_required(notation_view), {'mode': 'create'}, name='notation_create'),
    path('notations/<int:notation_id>/edit/', login_required(notation_view), {'mode': 'edit'}, name='notation_edit'),
    path('notations/<int:notation_id>/new_path/', login_required(new_notation_path),  name='new_notation_path'),
    path('notations/<int:notation_id>/new_id/', login_required(new_notation_ImportantDevelopment),  name='new_notation_ImportantDevelopment'),
    path('notations/<int:notation_id>/view/', login_required(notation_view), {'mode': 'view'}, name='notation_view'),
    path('notations/<int:notation_id>/new_comment/', login_required(new_notation_comment), name='new_notation_comment'),
    # path('paths/<int:path_id>/', login_required(path), name='path_vew'),
    path('paths/<int:path_id>/new_docs', login_required(new_path_docs), name='new_path_docs'),
    path('paths/<int:path_id>/', login_required(delete_path), name='delete_path'),
    path('AdministrativeInvestigations/', login_required(AdministrativeInvestigations_list), name='administrative_investigations_list'),
    path('AdministrativeInvestigations/create/', login_required(AdministrativeInvestigations_view), {'mode': 'create'}, name='administrative_investigation_create'),
    path('AdministrativeInvestigations/<int:administrative_investigation_id>/edit/', login_required(AdministrativeInvestigations_view), {'mode': 'edit'}, name='administrative_investigation_edit'),
    path('AdministrativeInvestigations/<int:administrative_investigation_id>/new_path/', login_required(new_AdministrativeInvestigation_path), name='new_administrative_investigation_path'),
    path('AdministrativeInvestigations/<int:administrative_investigation_id>/view/', login_required(AdministrativeInvestigations_view), {'mode': 'view'}, name='administrative_investigation_view'),
    path('AdministrativeInvestigations/<int:administrative_investigation_id>/new_id/', login_required(new_AdministrativeInvestigation_ImportantDevelopment),  name='new_AdministrativeInvestigation_ImportantDevelopment'),
    path('AdministrativeInvestigations/<int:pk>/', login_required(delete_AdministrativeInvestigation), name='delete_AdministrativeInvestigation'),
    path('tasks/', login_required(tasks_list), name='tasks_list'),
    path('tasks/create/', login_required(task_view), {'mode': 'create'},name='task_create'),
    path('tasks/<int:pk>/', login_required(delete_task), name='delete_task'),
    path('tasks/<int:task_id>/edit/', login_required(task_view),{'mode': 'edit'}, name='task_edit'),
    path('tasks/<int:task_id>/view/', login_required(task_view),{'mode': 'view'},name= 'task_view'),
    path('tasks/<int:task_id>/new_comment/', login_required(new_task_comment),name= 'new_task_comment'),
    path('tasks/<int:task_id>/new_path/', login_required(new_task_path),name= 'new_task_path'),
    path('hearings/', login_required(hearings_list), name='hearings_list'),
    path('hearing/<int:pk>/', login_required(delete_hearing), name='delete_hearing'),
    path('comments/<int:comment_id>/new_reply', login_required(new_comment_reply), name='new_comment_reply'),
    path('hearings/create/', login_required(hearing_view), {'mode': 'create'}, name='hearing_create'),
    path('hearings/<int:hearing_id>/edit', login_required(hearing_view),{'mode':'edit'}, name='hearing_edit'),
    path('hearings/<int:hearing_id>/view', login_required(hearing_view),{'mode':'view'}, name='hearing_view'),
    path('hearings/<int:hearing_id>/new_comment', login_required(new_hearing_comment), name='new_hearing_comment'),
    path('contracts/', login_required(contracts_list), name='contracts_list'),
    path('contracts/create', login_required(create_contract_with_payments), name='contract_create'),
    path('contracts/<int:contract_id>/edit', login_required(contract_view),{'mode':'edit'}, name='contract_edit'),
    path('contracts/<int:contract_id>/view', login_required(contract_view),{'mode':'view'}, name='contract_view'),
    path('contracts/<int:contract_id>/new_id/', login_required(new_contract_ImportantDevelopment),
         name='new_contract_ImportantDevelopment'),
    path('contracts/<int:contract_id>/new_comment', login_required(new_contract_comment), name='new_contract_comment'),
    path('paths/', login_required(Paths_list), name='paths_list'),
    path('docs/<int:doc_id>/images', login_required(doc_images), name='doc_images'),
    path('open/<path:filename>/', open_document, name='open_document'),
    path('contracts/<int:pk>/', login_required(delete_contract), name='delete_contract'),
    path("load-more-notifications/", load_more_notifications, name="load_more_notifications"),
    path("notifications/read_all", read_all_notifications, name="read_all_notifications"),
    path("notifications/<int:notification_id>/read", read_notification, name="read_notification"),
    path("notifications/delete_all", delete_all_notifications, name="delete_all_notifications"),
    path("notifications/<int:notification_id>/delete", delete_notification, name="delete_notification"),
    path('about/',about,name='about'),
    path('lang/', include('rosetta.urls')),
    path('notifications/', views.notifications),
    path('admin/', admin.site.urls),
    path('sentry-debug/', trigger_error),
    path('wizard/', ContactWizard.as_view([ContactForm1, ContactForm2],condition_dict={'1': show_message_form_condition}),),
    # path('account/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('service-worker.js', views.service_worker_view ,)
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]