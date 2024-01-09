import logging
import pandas as pd

from django.db.models import Q
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from im_export.views import check_user_rights
from individual.apps import IndividualConfig
from individual.models import IndividualDataSource
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
            raise ValueError('{}: {}'.format(result.get("message"), result.get("details")))

        return Response(result)
    except ValueError as e:
        logger.error("Error while uploading individuals", exc_info=e)
        return Response({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.error("Unexpected error while uploading individuals", exc_info=e)
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(["POST"])
@permission_classes([check_user_rights(IndividualConfig.gql_individual_create_perms, )])
def validate_import_beneficiaries(request):
    try:
        user = request.user
        upload_id, individual_sources, benefit_plan = _resolve_validate_import_beneficiaries_args(request)

        result = BeneficiaryImportService(user).validate_import_beneficiaries(
            upload_id,
            individual_sources,
            benefit_plan
        )
        if not result.get('success'):
            raise ValueError('{}: {}'.format(result.get("message"), result.get("details")))

        # for now just return info if df valid
        return Response(result)
    except ValueError as e:
        logger.error("Error while validating individuals", exc_info=e)
        return Response({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.error("Unexpected error while validating individuals", exc_info=e)
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(["POST"])
@permission_classes([check_user_rights(IndividualConfig.gql_individual_create_perms, )])
def create_task_with_importing_valid_items(request):
    try:
        user = request.user
        upload_id, benefit_plan = _resolve_create_task_with_importing_valid_items(request)
        BeneficiaryImportService(user).create_task_with_importing_valid_items(
            upload_id,
            benefit_plan
        )
        return Response({'success': True, 'error': None}, status=201)
    except ValueError as exc:
        logger.error("Error while sending callback to openIMIS", exc_info=exc)
        return Response({'success': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        logger.error("Unexpected error while sending callback to openIMIS", exc_info=exc)
        return Response({'success': False, 'error': str(exc)}, status=500)


@api_view(["GET"])
def download_invalid_items(request):
    try:
        upload_id = request.query_params.get('upload_id')

        invalid_items = IndividualDataSource.objects.filter(
            Q(is_deleted=False) &
            Q(upload_id=upload_id) &
            ~Q(validations__validation_errors=[])
        )

        data_from_source = []
        for invalid_item in invalid_items:
            json_ext = invalid_item.json_ext
            invalid_item.json_ext["id"] = invalid_item.id
            invalid_item.json_ext["error"] = invalid_item.validations
            data_from_source.append(json_ext)

        recreated_df = pd.DataFrame(data_from_source)
        csv_content = recreated_df.to_csv(index=False)

        # Create an HTTP response with the CSV content
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="invalid_items.csv"'
        return response

    except ValueError as exc:
        # Handle errors gracefully
        logger.error("Error while fetching data", exc_info=exc)
        return Response({'success': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        logger.error("Unexpected error", exc_info=exc)
        return Response({'success': False, 'error': str(exc)}, status=500)


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
        raise ValueError('{}: {}'.format(result.get("message"), result.get("details")))

    workflows = result.get('data', {}).get('workflows')

    if not workflows:
        raise ValueError('Workflow not found: group={} name={}'.format(workflow_group, workflow_name))
    if len(workflows) > 1:
        raise ValueError('Multiple workflows found: group={} name={}'.format(workflow_group, workflow_name))

    workflow = workflows[0]
    benefit_plan = BenefitPlan.objects.filter(uuid=benefit_plan_uuid).first()

    if not benefit_plan:
        raise ValueError('Benefit Plan not found: {}'.format(benefit_plan_uuid))

    return import_file, workflow, benefit_plan


def _resolve_validate_import_beneficiaries_args(request):
    benefit_plan_uuid = request.data.get('benefit_plan')
    upload_id = request.data.get('upload_id')

    benefit_plan = BenefitPlan.objects.filter(uuid=benefit_plan_uuid, is_deleted=False).first()
    individual_sources = IndividualDataSource.objects.filter(upload_id=upload_id)

    if not benefit_plan:
        raise ValueError('Benefit Plan not found: {}'.format(benefit_plan_uuid))

    return upload_id, individual_sources, benefit_plan


def _resolve_create_task_with_importing_valid_items(request):
    benefit_plan_uuid = request.data.get('benefit_plan')
    upload_id = request.data.get('upload_id')

    benefit_plan = BenefitPlan.objects.filter(uuid=benefit_plan_uuid, is_deleted=False).first()

    if not benefit_plan:
        raise ValueError('Benefit Plan not found: {}'.format(benefit_plan_uuid))

    return upload_id, benefit_plan
