from django.urls import path, include
from rest_framework import routers
from . import views
from django.conf.urls.i18n import i18n_patterns

router = routers.DefaultRouter()
router.register(r'litigationcases', views.LitigationCasesViewSet,"Litigation cases")
router.register(r'practice_area', views.practice_areaViewSet,"practice_area")
router.register(r'stages', views.stagesViewSet,"stages")
router.register(r'company', views.companyViewSet,"company")


urlpatterns = [
    path('', include(router.urls)),

]