import logging

from core.models import User
from tasks_management.models import Task
from social_protection.apps import SocialProtectionConfig
from social_protection.models import BenefitPlan, BenefitPlanDataUploadRecords
from workflow.services import WorkflowService

logger = logging.getLogger(__name__)


def on_task_complete_validation_import_valid_items(**kwargs):
    def validation_import_valid_items(upload_id, benefit_plan, user):
        workflow_name = SocialProtectionConfig.validation_import_valid_items_workflow
        result_workflow = WorkflowService.get_workflows(workflow_name, workflow_name)
        if not result_workflow.get('success'):
            raise ValueError('{}: {}'.format(result_workflow.get("message"), result_workflow.get("details")))

        workflows = result_workflow.get('data', {}).get('workflows')

        if not workflows:
            raise ValueError('Workflow not found: group={} name={}'.format(workflow_name, workflow_name))
        if len(workflows) > 1:
            raise ValueError('Multiple workflows found: group={} name={}'.format(workflow_name, workflow_name))

        workflow = workflows[0]
        workflow.run({
            # Core user UUID required
            'user_uuid': str(user.id),
            'benefit_plan_uuid': str(benefit_plan.uuid),
            'upload_uuid': str(upload_id),
        })

    try:
        result = kwargs.get('result', None)
        task = result['data']['task']
        if result \
                and result['success'] \
                and task['business_event'] == SocialProtectionConfig.validation_import_valid_items:
            task_status = task['status']
            if task_status == Task.Status.COMPLETED:
                user = User.objects.get(id=result['data']['user']['id'])
                upload_record = BenefitPlanDataUploadRecords.objects.get(id=task['entity_id'])
                benefit_plan = upload_record.benefit_plan
                upload_id = upload_record.data_upload.id
                validation_import_valid_items(upload_id, benefit_plan, user)
    except Exception as exc:
        logger.error("Error while executing on_validation_import_valid_items", exc_info=exc)
