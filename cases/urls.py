from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'cases'

router = routers.DefaultRouter()
router.register(r'litigationcases', views.LitigationCasesViewSet, "Litigation cases")
router.register(r'administrative_investigation', views.AdministrativeInvestigationsViewSet, "Administrative Investigations")
router.register(r'notation', views.NotationViewSet, "Notation")
router.register(r'Folders', views.FoldersViewSet, "Folders")
router.register(r'case_type', views.case_typeViewSet, "case_type")
router.register(r'characteristic', views.characteristicViewSet, "characteristic")
router.register(r'stages', views.stagesViewSet, "stages")
router.register(r'courts', views.courtViewSet, "courts")
router.register(r'opponent_position', views.opponent_positionViewSet, "opponent_position")
router.register(r'client_position', views.client_positionViewSet, "client_position")
router.register(r'ImportantDevelopments', views.ImportantDevelopmentsViewSet, "ImportantDevelopments")

urlpatterns = [
    path('', include(router.urls)),

    # path(r'case/new/', views.case, name='case_new'),
    # path(r'case/edit/<case_id>/', views.case, name='case_edit'),
]
