import jsonschema

from django.core.exceptions import ValidationError

from gettext import gettext as _
from core.validation import BaseModelValidation
from social_protection.models import BenefitPlan


class BenefitPlanValidation(BaseModelValidation):
    OBJECT_TYPE = BenefitPlan

    @classmethod
    def validate_create(cls, user, **data):
        errors = validate_benefit_plan(data)
        if errors:
            raise ValidationError(errors)
        super().validate_create(user, **data)

    @classmethod
    def validate_update(cls, user, **data):
        uuid = data.get('id')
        errors = validate_benefit_plan(data, uuid)
        if errors:
            raise ValidationError(errors)
        super().validate_update(user, **data)

    @classmethod
    def validate_delete(cls, user, **data):
        super().validate_delete(user, **data)


def validate_benefit_plan(data, uuid=None):
    return [
        *validate_not_empty_field(data.get("code"), "code"),
        *validate_bf_unique_code(data.get('code'), uuid),
        *validate_not_empty_field(data.get("name"), "name"),
        *validate_bf_unique_name(data.get('name'), uuid),
        *validate_json_schema(data.get('beneficiary_data_schema'))
    ]


def validate_bf_unique_code(code, uuid=None):
    instance = BenefitPlan.objects.filter(code=code, is_deleted=False).first()
    if instance and instance.uuid != uuid:
        return [{"message": _("social_protection.validation.benefit_plan.code_exists" % {
            'code': code
        })}]
    return []


def validate_bf_unique_name(name, uuid=None):
    instance = BenefitPlan.objects.filter(name=name, is_deleted=False).first()
    if instance and instance.uuid != uuid:
        return [{"message": _("social_protection.validation.benefit_plan.name_exists" % {
            'name': name
        })}]
    return []


def validate_json_schema(schema):
    try:
        jsonschema.Draft7Validator.check_schema(schema)
        return []
    except jsonschema.exceptions.SchemaError as e:
        return [{"message": _("social_protection.validation.benefit_plan.invalid_schema" % {
            'error': e
        })}]


def validate_not_empty_field(string, field):
    if not string:
        return [{"message": _("social_protection.validation.field_empty") % {
            'field': field
        }}]
    return []
