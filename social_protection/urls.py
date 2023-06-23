from django.urls import path

from .views import import_beneficiaries

urlpatterns = [
    path('import_beneficiaries/', import_beneficiaries),
]
