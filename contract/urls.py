from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'contract'

router = routers.DefaultRouter()
router.register(r'contract', views.ContractViewSet, "Contracts")
router.register(r'Payment', views.PaymentViewSet, "Payment")
router.register(r'Duration', views.DurationViewSet, "Duration")
router.register(r'Type', views.TypeViewSet, "Type")

urlpatterns = [
    path('', include(router.urls)),
]