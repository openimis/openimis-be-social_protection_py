import logging

from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal
from social_protection.services import BenefitPlanService, BeneficiaryService, GroupBeneficiaryService

from social_protection.signals.on_benefit_plan_data_upload import on_benefit_plan_data_upload
# from social_protection.signals.on_validation_import import on_task_complete_validation_import_valid_items
from tasks_management.services import on_task_complete_service_handler
from social_protection.apps import SocialProtectionConfig
from core.models import User
from workflow.services import WorkflowService
from task.models import Task

logger = logging.getLogger(__name__)


def bind_service_signals():
    def on_task_complete_validation_import_valid_items(**kwargs):
        def validation_import_valid_items(upload_id, benefit_plan, user):
            workflow_name = SocialProtectionConfig.validation_import_valid_items_workflow
            logger.debug(workflow_name)
            result_workflow = WorkflowService.get_workflows(workflow_name, workflow_name)
            logger.error(result_workflow)
            if not result_workflow.get('success'):
                raise ValueError('{}: {}'.format(result_workflow.get("message"), result_workflow.get("details")))

            workflows = result_workflow.get('data', {}).get('workflows')

            if not workflows:
                raise ValueError('Workflow not found: group={} name={}'.format(workflow_name, workflow_name))
            if len(workflows) > 1:
                raise ValueError('Multiple workflows found: group={} name={}'.format(workflow_name, workflow_name))

            workflow = workflows[0]
            logger.error('workflow')
            logger.error(workflow)
            workflow.run({
                # Core user UUID required
                'user_uuid': str(user.id),
                'benefit_plan_uuid': str(benefit_plan.uuid),
                'upload_uuid': str(upload_id),
            })

        try:
            result = kwargs.get('result', None)
            benefit_plan = kwargs['data'][0][0]
            upload_id = kwargs['data'][0][1]
            task = result['data']['task']
            user = User.objects.get(id=result['data']['user']['id'])
            if result \
                    and result['success'] \
                    and task['business_event'] == SocialProtectionConfig.validation_import_valid_items:
                task_status = task['status']
                if task_status == Task.Status.COMPLETED:
                    validation_import_valid_items(upload_id, benefit_plan, user)
        except Exception as exc:
            logger.error("Error while executing on_validation_import_valid_items", exc_info=exc)


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
