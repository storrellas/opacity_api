from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'company', CompanyViewSet, basename='company')
urlpatterns = router.urls

urlpatterns = [
  path('company/<str:pk>/pivottable/', CompanyPivotTableApiView.as_view()),
  path('company/<str:pk>/raw/', CompanyRawApiView.as_view()),
  path('company/<str:pk>/import/', CompanyImportView.as_view()),
  
]
urlpatterns += router.urls


