import logging

from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal
from social_protection.services import BenefitPlanService, BeneficiaryService, GroupBeneficiaryService

from social_protection.signals.on_benefit_plan_data_upload import on_benefit_plan_data_upload
from social_protection.signals.on_validation_import import on_task_complete_validation_import_valid_items
from tasks_management.services import on_task_complete_service_handler

logger = logging.getLogger(__name__)


def bind_service_signals():
    bind_service_signal(
        'benefit_plan.import_beneficiaries',
        on_benefit_plan_data_upload,
        bind_type=ServiceSignalBindType.AFTER
    )
    bind_service_signal(
        'task_service.complete_task',
        on_task_complete_service_handler(BenefitPlanService),
        bind_type=ServiceSignalBindType.AFTER
    )
    bind_service_signal(
        'task_service.complete_task',
        on_task_complete_service_handler(BeneficiaryService),
        bind_type=ServiceSignalBindType.AFTER
    )
    bind_service_signal(
        'task_service.complete_task',
        on_task_complete_service_handler(GroupBeneficiaryService),
        bind_type=ServiceSignalBindType.AFTER
    )
    bind_service_signal(
        'task_service.complete_task',
        on_task_complete_validation_import_valid_items,
        bind_type=ServiceSignalBindType.AFTER
    )
