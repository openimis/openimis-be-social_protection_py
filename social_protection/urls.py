from django.urls import path

from .views import import_beneficiaries, validate_import_beneficiaries

urlpatterns = [
    path('import_beneficiaries/', import_beneficiaries),
    path('validate_import_beneficiaries/', validate_import_beneficiaries),
]
