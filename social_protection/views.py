import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from im_export.views import check_user_rights
from individual.apps import IndividualConfig
from social_protection.models import BenefitPlan
from social_protection.services import BeneficiaryImportService
from workflow.services import WorkflowService

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([check_user_rights(IndividualConfig.gql_individual_create_perms, )])
def import_beneficiaries(request):
    try:
        user = request.user
        import_file, workflow, benefit_plan = _resolve_import_beneficiaries_args(request)

        result = BeneficiaryImportService(user).import_beneficiaries(import_file, benefit_plan, workflow)
        if not result.get('success'):
            raise ValueError(f'{result.get("message")}: {result.get("details")}')

        return Response(result)
    except ValueError as e:
        logger.error("Error while uploading individuals", exc_info=e)
        return Response({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.error("Unexpected error while uploading individuals", exc_info=e)
        return Response({'success': False, 'error': str(e)}, status=500)


def _resolve_import_beneficiaries_args(request):
    import_file = request.FILES.get('file')
    benefit_plan_uuid = request.POST.get('benefit_plan')
    workflow_name = request.POST.get('workflow_name')
    workflow_group = request.POST.get('workflow_group')

    if not import_file:
        raise ValueError(f'Import file not provided')
    if not benefit_plan_uuid:
        raise ValueError(f'Benefit plan UUID not provided')
    if not workflow_name:
        raise ValueError(f'Workflow name not provided')
    if not workflow_group:
        raise ValueError(f'Workflow group not provided')

    result = WorkflowService.get_workflows(workflow_name, workflow_group)
    if not result.get('success'):
        raise ValueError(f'{result.get("message")}: {result.get("details")}')

    workflows = result.get('data', {}).get('workflows')

    if not workflows:
        raise ValueError(f'Workflow not found: group={workflow_group} name={workflow_name}')
    if len(workflows) > 1:
        raise ValueError(f'Multiple workflows found: group={workflow_group} name={workflow_name}')

    workflow = workflows[0]
    benefit_plan = BenefitPlan.objects.filter(uuid=benefit_plan_uuid).first()

    if not benefit_plan:
        raise ValueError(f'Benefit Plan not found: {benefit_plan_uuid}')

    return import_file, workflow, benefit_plan
