from django.urls import path

from .views import (
    import_beneficiaries,
    validate_import_beneficiaries,
    create_task_with_importing_valid_items
)

urlpatterns = [
    path('import_beneficiaries/', import_beneficiaries),
    path('validate_import_beneficiaries/', validate_import_beneficiaries),
    path('create_task_with_importing_valid_items/', create_task_with_importing_valid_items),
]
