import logging

from core.services import BaseService
from core.signals import register_service_signal
from individual.models import IndividualDataSourceUpload
from social_protection.models import (
    BenefitPlan,
    Beneficiary, GroupBeneficiary
)
from social_protection.validation import (
    BeneficiaryValidation,
    BenefitPlanValidation, GroupBeneficiaryValidation
)

logger = logging.getLogger(__name__)


class BenefitPlanService(BaseService):
    OBJECT_TYPE = BenefitPlan

    def __init__(self, user, validation_class=BenefitPlanValidation):
        super().__init__(user, validation_class)

    @register_service_signal('benefit_plan_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('benefit_plan_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('benefit_plan_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)


class BeneficiaryService(BaseService):
    OBJECT_TYPE = Beneficiary

    def __init__(self, user, validation_class=BeneficiaryValidation):
        super().__init__(user, validation_class)

    @register_service_signal('beneficiary_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('beneficiary_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('beneficiary_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)


class GroupBeneficiaryService(BaseService):
    OBJECT_TYPE = GroupBeneficiary

    def __init__(self, user, validation_class=GroupBeneficiaryValidation):
        super().__init__(user, validation_class)

    @register_service_signal('group_beneficiary_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('group_beneficiary_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('group_beneficiary_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)


class BeneficiaryImportService:
    def __init__(self, user):
        super().__init__()
        self.user = user

    def import_beneficiaries(self, import_file, benefit_plan, workflow):
        source_name = import_file.name
        source_type = 'beneficiary import'
        upload = IndividualDataSourceUpload(
            source_name=source_name,
            source_type=source_type
        )
        upload.save(username=self.user.login_name)

        return {'success': True, 'data': {'upload_uuid': upload.uuid}}


