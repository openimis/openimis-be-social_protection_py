import logging

from django.core.exceptions import ValidationError

from core.services import BaseService
from core.signals import register_service_signal
from social_protection.models import BenefitPlan
from social_protection.validation import BenefitPlanValidation

logger = logging.getLogger(__name__)


class BenefitPlanService(BaseService):
    @register_service_signal('benefit_plan_service.create')
    def create(self, obj_data):
        incoming_code = obj_data.get('code')
        if check_unique_code(incoming_code):
            raise ValidationError(("Benefit code %s already exists" % incoming_code))
        incoming_name = obj_data.get('name')
        if check_unique_name(incoming_name):
            raise ValidationError(("Benefit name %s already exists" % incoming_name))
        return super().create(obj_data)

    @register_service_signal('benefit_plan_service.update')
    def update(self, obj_data):
        uuid = obj_data.get('id')
        incoming_code = obj_data.get('code')
        if check_unique_code(incoming_code, uuid):
            raise ValidationError(("Benefit code %s already exists" % incoming_code))
        incoming_name = obj_data.get('name')
        if check_unique_name(incoming_name, uuid):
            raise ValidationError(("Benefit name %s already exists" % incoming_name))
        return super().update(obj_data)

    @register_service_signal('benefit_plan_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)

    OBJECT_TYPE = BenefitPlan

    def __init__(self, user, validation_class=BenefitPlanValidation):
        super().__init__(user, validation_class)


def check_unique_code(code, uuid=None):
    instance = BenefitPlan.objects.get(code=code, is_deleted=False)
    if instance and instance.uuid != uuid:
        return [{"message": "BenefitPlan code %s already exists" % code}]
    return []


def check_unique_name(name, uuid=None):
    instance = BenefitPlan.objects.get(name=name, is_deleted=False)
    if instance and instance.uuid != uuid:
        return [{"message": "BenefitPlan name %s already exists" % name}]
    return []
