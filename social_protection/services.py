from core.services import BaseService
from social_protection.models import BenefitPlan
from social_protection.validation import BenefitPlanValidation


class BenefitPlanService(BaseService):
    OBJECT_TYPE = BenefitPlan

    def __init__(self, user, validation_class=BenefitPlanValidation):
        super().__init__(user, validation_class)
