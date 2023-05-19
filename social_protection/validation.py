from django.core.exceptions import ValidationError

from core.validation import BaseModelValidation
from social_protection.models import BenefitPlan


class BenefitPlanValidation(BaseModelValidation):
    OBJECT_TYPE = BenefitPlan

    @classmethod
    def validate_create(cls, user, **data):
        incoming_code = data.get('code')
        if check_bf_unique_code(incoming_code):
            raise ValidationError(("Benefit code %s already exists" % incoming_code))
        incoming_name = data.get('name')
        if check_bf_unique_name(incoming_name):
            raise ValidationError(("Benefit name %s already exists" % incoming_name))
        super().validate_create(user, **data)

    @classmethod
    def validate_update(cls, user, **data):
        uuid = data.get('id')
        incoming_code = data.get('code')
        if check_bf_unique_code(incoming_code, uuid):
            raise ValidationError(("Benefit code %s already exists" % incoming_code))
        incoming_name = data.get('name')
        if check_bf_unique_name(incoming_name, uuid):
            raise ValidationError(("Benefit name %s already exists" % incoming_name))
        super().validate_update(user, **data)

    @classmethod
    def validate_delete(cls, user, **data):
        super().validate_delete(user, **data)


def check_bf_unique_code(code, uuid=None):
    instance = BenefitPlan.objects.filter(code=code, is_deleted=False).first()
    if instance and instance.uuid != uuid:
        return [{"message": "BenefitPlan code %s already exists" % code}]
    return []


def check_bf_unique_name(name, uuid=None):
    instance = BenefitPlan.objects.filter(name=name, is_deleted=False).first()
    if instance and instance.uuid != uuid:
        return [{"message": "BenefitPlan name %s already exists" % name}]
    return []
