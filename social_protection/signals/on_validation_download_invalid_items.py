import logging
import pandas as pd

from django.db.models import Q
from django.http import HttpResponse

from core.models import User
from tasks_management.models import Task
from social_protection.apps import SocialProtectionConfig
from social_protection.models import BenefitPlanDataUploadRecords
from individual.models import IndividualDataSource

logger = logging.getLogger(__name__)


def on_task_complete_validation_download_invalid_items(**kwargs):
    def validation_download_invalid_items(upload_id, benefit_plan, user):
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
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="invalid_items.csv"'
        logger.info(response)
        return response

    try:
        result = kwargs.get('result', None)
        task = result['data']['task']
        if result \
                and result['success'] \
                and task['business_event'] == SocialProtectionConfig.validation_download_invalid_items:
            task_status = task['status']
            if task_status == Task.Status.COMPLETED:
                user = User.objects.get(id=result['data']['user']['id'])
                upload_record = BenefitPlanDataUploadRecords.objects.get(id=task['entity_id'])
                benefit_plan = upload_record.benefit_plan
                upload_id = upload_record.data_upload.id
                return validation_download_invalid_items(upload_id, benefit_plan, user)
    except Exception as exc:
        logger.error("Error while executing on_validation_import_valid_items", exc_info=exc)
