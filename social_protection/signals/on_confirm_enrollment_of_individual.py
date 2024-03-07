import logging

from django.core.exceptions import ValidationError
from social_protection.apps import SocialProtectionConfig
from social_protection.models import Beneficiary
from social_protection.services import BeneficiaryService

logger = logging.getLogger(__name__)


def on_confirm_enrollment_of_individual(**kwargs):
    result = kwargs.get('result', None)
    benefit_plan_id = result['benefit_plan_id']
    status = result['status']
    user = result['user']
    individuals_to_upload = result['individuals_not_assigned_to_selected_programme']
    if SocialProtectionConfig.enable_maker_checker_logic_enrollment:
        for individual in individuals_to_upload:
            input_data = {
                "individual_id":  individual.id,
                "benefit_plan_id": benefit_plan_id,
                "status": status,
                "json_ext": individual.json_ext
            }
            BeneficiaryService(user).create_create_task(input_data)
    else:
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

