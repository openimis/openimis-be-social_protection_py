import copy
from individual.models import Individual
from social_protection.models import BenefitPlan
from social_protection.tests.data import (
    service_add_payload_valid_schema,
    service_beneficiary_add_payload,
    service_add_individual_payload_with_ext,
)

def merge_dicts(original, override):
    updated = copy.deepcopy(original)
    for key, value in override.items():
        if isinstance(value, dict) and key in updated:
            updated[key] = merge_dicts(updated.get(key, {}), value)
        else:
            updated[key] = value
    return updated

def create_benefit_plan(username, payload_override={}):
    updated_payload = merge_dicts(service_add_payload_valid_schema, payload_override)
    benefit_plan = BenefitPlan(**updated_payload)
    benefit_plan.save(username=username)

    return benefit_plan

def create_individual(username, payload_override={}):
    updated_payload = merge_dicts(service_add_individual_payload_with_ext, payload_override)
    individual = Individual(**updated_payload)
    individual.save(username=username)

    return individual

def add_individual_to_benefit_plan(service, individual, benefit_plan, payload_override={}):
    payload = {
        **service_beneficiary_add_payload,
        "individual_id": individual.id,
        "benefit_plan_id": benefit_plan.id,
        "json_ext": individual.json_ext,
    }
    updated_payload = merge_dicts(payload, payload_override)
    result = service.create(updated_payload)
    assert result.get('success', False), result.get('detail', "No details provided")
    uuid = result.get('data', {}).get('uuid', None)
    return uuid
