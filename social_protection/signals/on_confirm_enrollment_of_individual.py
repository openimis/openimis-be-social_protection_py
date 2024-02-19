import logging

from django.core.exceptions import ValidationError
from social_protection.models import Beneficiary

logger = logging.getLogger(__name__)


def on_confirm_enrollment_of_individual(**kwargs):
    result = kwargs.get('result', None)
    benefit_plan_id = result['benefit_plan_id']
    status = result['status']
    user = result['user']
    individuals_to_upload = result['individuals_not_assigned_to_selected_programme']
    for individual in individuals_to_upload:
        # Create a new Beneficiary instance
        beneficiary = Beneficiary(
            individual=individual,
            benefit_plan_id=benefit_plan_id,
            status=status,
            json_ext=individual.json_ext
        )
        try:
            beneficiary.save(username=user.username)
        except ValidationError as e:
            logger.error(f"Validation error occurred: {e}")
