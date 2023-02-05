from django.urls import path, include
from rest_framework import routers
from . import views
from django.conf.urls.i18n import i18n_patterns

router = routers.DefaultRouter()
router.register(r'task', views.taskViewSet,"task")
# router.register(r'task_type', views.task_typeViewSet,"task_type")
# router.register(r'event', views.eventViewSet,"event")
# router.register(r'event_type', views.event_typeViewSet,"event_type")
router.register(r'hearing', views.hearingViewSet,"hearing")
# router.register(r'hearing_type', views.hearing_typeViewSet,"hearing_type")


urlpatterns = [
    path('', include(router.urls)),

]