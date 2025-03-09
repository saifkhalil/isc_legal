from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'task', views.taskViewSet, "task")
router.register(r'hearing', views.hearingViewSet, "hearing")

urlpatterns = [
    path('', include(router.urls)),
]
