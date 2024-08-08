from individual.models import Individual
from social_protection.models import BenefitPlan
from social_protection.tests.data import (
    service_add_payload_valid_schema,
    service_beneficiary_add_payload,
    service_add_individual_payload_with_ext,
)

def create_benefit_plan(username):
    benefit_plan = BenefitPlan(**service_add_payload_valid_schema)
    benefit_plan.save(username=username)

    return benefit_plan

def create_individual(username):
    individual = Individual(**service_add_individual_payload_with_ext)
    individual.save(username=username)

    return individual

def add_individual_to_benefit_plan(service, individual, benefit_plan):
    payload = {
        **service_beneficiary_add_payload,
        "individual_id": individual.id,
        "benefit_plan_id": benefit_plan.id,
        "json_ext": individual.json_ext,
    }
    result = service.create(payload)
    assert result.get('success', False), result.get('detail', "No details provided")
    uuid = result.get('data', {}).get('uuid', None)
    return uuid
