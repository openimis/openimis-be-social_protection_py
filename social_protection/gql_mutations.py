import graphene as graphene
from django.contrib.auth.models import AnonymousUser
from pydantic.error_wrappers import ValidationError
from django.db import transaction

from core.gql.gql_mutations.base_mutation import BaseHistoryModelCreateMutationMixin, BaseMutation, \
    BaseHistoryModelUpdateMutationMixin, BaseHistoryModelDeleteMutationMixin
from core.schema import OpenIMISMutation
from social_protection.apps import SocialProtectionConfig
from social_protection.models import (
    BenefitPlan,
    Beneficiary
)
from social_protection.services import (
    BenefitPlanService,
    BeneficiaryService
)


class CreateBenefitPlanInputType(OpenIMISMutation.Input):
    code = graphene.String(required=True)
    name = graphene.String(required=True, max_length=255)
    max_beneficiaries = graphene.Int(default_value=0)
    ceiling_per_beneficiary = graphene.Decimal(max_digits=18, decimal_places=2, required=False)
    holder_id = graphene.UUID(required=False)
    beneficiary_data_schema = graphene.types.json.JSONString(required=False)

    date_valid_from = graphene.Date(required=True)
    date_valid_to = graphene.Date(required=True)
    json_ext = graphene.types.json.JSONString(required=False)


class UpdateBenefitPlanInputType(CreateBenefitPlanInputType):
    id = graphene.UUID(required=True)


class CreateBeneficiaryInputType(OpenIMISMutation.Input):
    status = graphene.String(required=True)
    individual_id = graphene.UUID(required=False)
    benefit_plan_id = graphene.UUID(required=False)

    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class UpdateBeneficiaryInputType(CreateBeneficiaryInputType):
    id = graphene.UUID(required=True)


class CreateBenefitPlanMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "CreateBenefitPlanMutation"
    _mutation_module = "social_protection"
    _model = BenefitPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.has_perms(
                SocialProtectionConfig.gql_benefit_plan_create_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = BenefitPlanService(user)
        service.create(data)

    class Input(CreateBenefitPlanInputType):
        pass


class UpdateBenefitPlanMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "UpdateBenefitPlanMutation"
    _mutation_module = "social_protection"
    _model = BenefitPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if type(user) is AnonymousUser or not user.has_perms(
                SocialProtectionConfig.gql_benefit_plan_update_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "date_valid_to" not in data:
            data['date_valid_to'] = None
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = BenefitPlanService(user)
        service.update(data)

    class Input(UpdateBenefitPlanInputType):
        pass


class DeleteBenefitPlanMutation(BaseHistoryModelDeleteMutationMixin, BaseMutation):
    _mutation_class = "DeleteBenefitPlanMutation"
    _mutation_module = "social_protection"
    _model = BenefitPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                SocialProtectionConfig.gql_benefit_plan_delete_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = BenefitPlanService(user)

        ids = data.get('ids')
        if ids:
            with transaction.atomic():
                for id in ids:
                    service.delete({'id': id})

    class Input(OpenIMISMutation.Input):
        ids = graphene.List(graphene.UUID)


class CreateBeneficiaryMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "CreateBeneficiaryMutation"
    _mutation_module = "social_protection"
    _model = Beneficiary

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.has_perms(
                SocialProtectionConfig.gql_beneficiary_create_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = BeneficiaryService(user)
        service.create(data)

    class Input(CreateBeneficiaryInputType):
        pass


class UpdateBeneficiaryMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "UpdateBeneficiaryMutation"
    _mutation_module = "social_protection"
    _model = Beneficiary

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if type(user) is AnonymousUser or not user.has_perms(
                SocialProtectionConfig.gql_beneficiary_update_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "date_valid_to" not in data:
            data['date_valid_to'] = None
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = BeneficiaryService(user)
        service.update(data)

    class Input(UpdateBeneficiaryInputType):
        pass


class DeleteBeneficiaryMutation(BaseHistoryModelDeleteMutationMixin, BaseMutation):
    _mutation_class = "DeleteBeneficiaryMutation"
    _mutation_module = "social_protection"
    _model = Beneficiary

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                SocialProtectionConfig.gql_beneficiary_delete_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = BeneficiaryService(user)

        ids = data.get('ids')
        if ids:
            with transaction.atomic():
                for id in ids:
                    service.delete({'id': id})

    class Input(OpenIMISMutation.Input):
        ids = graphene.List(graphene.UUID)
