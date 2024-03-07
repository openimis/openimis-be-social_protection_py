import logging

from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal
from social_protection.services import BenefitPlanService, BeneficiaryService, GroupBeneficiaryService
from social_protection.signals.on_validation_import_valid_items import on_task_complete_import_validated, \
    on_task_resolve
from tasks_management.services import on_task_complete_service_handler

logger = logging.getLogger(__name__)


def bind_service_signals():
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
        on_task_complete_import_validated,
        bind_type=ServiceSignalBindType.AFTER
    )
    bind_service_signal(
        'task_service.resolve_task',
        on_task_resolve,
        bind_type=ServiceSignalBindType.AFTER
    )
