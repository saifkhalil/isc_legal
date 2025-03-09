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
from django.shortcuts import render
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from . import views
from .views import (
    APIPathListView, APIPathView
)
from accounts.views import SearchEmployeeAPIView

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
                  

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += i18n_patterns(
    path('lang/', include('rosetta.urls')),
    path('notifications/', views.notifications),
    path('admin/', admin.site.urls),
    path('sentry-debug/', trigger_error),
    path('i18n/', include('django.conf.urls.i18n')),
    path('account/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')),
)
