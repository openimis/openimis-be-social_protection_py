from core.validation import BaseModelValidation
from social_protection.models import BenefitPlan


class BenefitPlanValidation(BaseModelValidation):
    OBJECT_TYPE = BenefitPlan

    @classmethod
    def validate_create(cls, user, **data):
        super().validate_create(user, **data)

    @classmethod
    def validate_update(cls, user, **data):
        super().validate_update(user, **data)

    @classmethod
    def validate_delete(cls, user, **data):
        super().validate_delete(user, **data)
