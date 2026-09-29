from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from core.validation import BaseModelValidation, ObjectExistsValidationMixin
from individual.validation import (
    schema_dict,
    schema_errors,
    schema_subset_errors,
)
from social_protection.models import Beneficiary, BenefitPlan, Project


class BenefitPlanValidation(BaseModelValidation, ObjectExistsValidationMixin):
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

    @classmethod
    def validate_undo_delete(cls, data):
        obj_id = data.get('id')
        cls.validate_object_exists(obj_id)
        obj = BenefitPlan.objects.get(id=obj_id)
        errors = [
            *validate_bf_unique_code(obj.code, obj_id),
            *validate_bf_unique_name(obj.name, obj_id),
        ]
        if errors:
            raise ValidationError(errors)


def validate_benefit_plan(data, uuid=None):
    validations = [
        *validate_not_empty_field(data.get("code"), "code"),
        *validate_bf_unique_code(data.get('code'), uuid),
        *validate_not_empty_field(data.get("name"), "name"),
        *validate_bf_unique_name(data.get('name'), uuid)
    ]

    beneficiary_data_schema = data.get('beneficiary_data_schema')
    if beneficiary_data_schema:
        validations.extend(
            validate_beneficiary_data_schema(beneficiary_data_schema, uuid)
        )

    return validations


def validate_beneficiary_data_schema(schema, uuid=None):
    """
    The individual schema's field rules, on fields of the individual schema.
    An update that leaves the stored schema as it is passes, so plans older
    than that rule keep working until their schema is edited.
    """
    parsed = schema_dict(schema)
    errors = schema_errors(parsed if parsed is not None else schema)
    if errors:
        return errors
    if uuid:
        stored = BenefitPlan.objects.filter(id=uuid) \
            .values_list('beneficiary_data_schema', flat=True).first()
        if schema_dict(stored) == parsed:
            return []
    return schema_subset_errors(parsed)


def validate_bf_unique_code(code, uuid=None):
    instance = BenefitPlan.objects.filter(
        code=code, is_deleted=False
    ).exclude(id=uuid).first()
    if instance:
        msg = "social_protection.validation.benefit_plan.code_exists"
        return [{"message": _(msg % {'code': code})}]  # noqa: F504
    return []


def validate_bf_unique_name(name, uuid=None):
    instance = BenefitPlan.objects.filter(
        name=name, is_deleted=False
    ).exclude(id=uuid).first()
    if instance:
        msg = "social_protection.validation.benefit_plan.name_exists"
        return [{"message": _(msg % {'name': name})}]  # noqa: F504
    return []


def validate_not_empty_field(string, field):
    if not string:
        return [{"message": _("social_protection.validation.field_empty") % {
            'field': field
        }}]
    return []


class BeneficiaryValidation(BaseModelValidation):
    OBJECT_TYPE = Beneficiary


class GroupBeneficiaryValidation(BaseModelValidation):
    OBJECT_TYPE = Beneficiary


def validate_project_unique_name(name, benefit_plan_id, uuid=None):
    instance = Project.objects.filter(
        name=name, benefit_plan__id=benefit_plan_id, is_deleted=False
    ).exclude(id=uuid).first()
    if instance:
        msg = "social_protection.validation.project.name_exists"
        return [{"message": _(msg % {'name': name})}]  # noqa: F504
    return []


class ProjectValidation(BaseModelValidation, ObjectExistsValidationMixin):
    OBJECT_TYPE = Project

    @classmethod
    def validate_undo_delete(cls, data):
        obj_id = data.get('id')
        cls.validate_object_exists(obj_id)
        obj = Project.objects.get(id=obj_id)
        errors = validate_project_unique_name(
            obj.name, obj.benefit_plan_id, obj_id
        )
        if errors:
            raise ValidationError(errors)
