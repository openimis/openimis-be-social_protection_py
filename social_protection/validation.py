import jsonschema

from django.core.exceptions import ValidationError

from core.validation import BaseModelValidation
from social_protection.models import BenefitPlan


class BenefitPlanValidation(BaseModelValidation):
    OBJECT_TYPE = BenefitPlan

    @classmethod
    def validate_create(cls, user, **data):
        incoming_code = data.get('code')
        code_error = check_bf_unique_code(incoming_code)
        if code_error:
            raise ValidationError(code_error[0]['message'])
        incoming_name = data.get('name')
        name_error = check_bf_unique_name(incoming_name)
        if name_error:
            raise ValidationError(name_error[0]['message'])
        incoming_schema = data.get('beneficiary_data_schema')
        schema_error = is_valid_json_schema(incoming_schema)
        if schema_error:
            raise ValidationError(schema_error[0]['message'])
        super().validate_create(user, **data)

    @classmethod
    def validate_update(cls, user, **data):
        uuid = data.get('id')
        incoming_code = data.get('code')
        code_error = check_bf_unique_code(incoming_code, uuid)
        if code_error:
            raise ValidationError(code_error[0]['message'])
        incoming_name = data.get('name')
        name_error = check_bf_unique_name(incoming_name, uuid)
        if name_error:
            raise ValidationError(name_error[0]['message'])
        incoming_schema = data.get('beneficiary_data_schema')
        schema_error = is_valid_json_schema(incoming_schema)
        if schema_error:
            raise ValidationError(schema_error[0]['message'])
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


def is_valid_json_schema(schema):
    try:
        jsonschema.Draft7Validator.check_schema(schema)
        return []
    except jsonschema.exceptions.SchemaError:
        return [{"message": "BenefitPlan schema is not valid"}]
