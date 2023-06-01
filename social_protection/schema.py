import graphene
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from django.utils.translation import gettext as _
from core.gql_queries import ValidationMessageGQLType
from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from social_protection.apps import SocialProtectionConfig
from social_protection.gql_mutations import (
    CreateBenefitPlanMutation,
    UpdateBenefitPlanMutation,
    DeleteBenefitPlanMutation,
    CreateBeneficiaryMutation,
    UpdateBeneficiaryMutation,
    DeleteBeneficiaryMutation
)
from social_protection.gql_queries import (
    BenefitPlanGQLType,
    BeneficiaryGQLType, GroupGQLType
)
from social_protection.models import (
    BenefitPlan,
    Beneficiary, Group
)
from social_protection.validation import validate_bf_unique_code, validate_bf_unique_name, validate_json_schema
import graphene_django_optimizer as gql_optimizer


class Query:
    benefit_plan = OrderedDjangoFilterConnectionField(
        BenefitPlanGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String()
    )
    beneficiary = OrderedDjangoFilterConnectionField(
        BeneficiaryGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String()
    )
    group = OrderedDjangoFilterConnectionField(
        GroupGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String()
    )
    bf_code_validity = graphene.Field(
        ValidationMessageGQLType,
        bf_code=graphene.String(required=True),
        description="Checks that the specified Benefit Plan code is valid"
    )
    bf_name_validity = graphene.Field(
        ValidationMessageGQLType,
        bf_name=graphene.String(required=True),
        description="Checks that the specified Benefit Plan name is valid"
    )
    bf_schema_validity = graphene.Field(
        ValidationMessageGQLType,
        bf_schema=graphene.String(required=True),
        description="Checks that the specified Benefit Plan schema is valid"
    )

    def resolve_bf_code_validity(self, info, **kwargs):
        Query._check_permissions(
            info.context.user,
            SocialProtectionConfig.gql_benefit_plan_search_perms
        )
        errors = validate_bf_unique_code(kwargs['bf_code'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_bf_name_validity(self, info, **kwargs):
        Query._check_permissions(
            info.context.user,
            SocialProtectionConfig.gql_benefit_plan_search_perms
        )
        errors = validate_bf_unique_name(kwargs['bf_name'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_bf_schema_validity(self, info, **kwargs):
        Query._check_permissions(
            info.context.user,
            SocialProtectionConfig.gql_benefit_plan_search_perms
        )
        errors = validate_json_schema(kwargs['bf_schema'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_benefit_plan(self, info, **kwargs):
        Query._check_permissions(
            info.context.user,
            SocialProtectionConfig.gql_benefit_plan_search_perms
        )
        filters = append_validity_filter(**kwargs)
        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        query = BenefitPlan.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    def resolve_beneficiary(self, info, **kwargs):
        Query._check_permissions(
            info.context.user,
            SocialProtectionConfig.gql_beneficiary_search_perms
        )
        filters = append_validity_filter(**kwargs)
        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        query = Beneficiary.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    def resolve_group(self, info, **kwargs):
        Query._check_permissions(
            info.context.user,
            SocialProtectionConfig.gql_group_search_perms
        )
        filters = append_validity_filter(**kwargs)
        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        query = Group.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    @staticmethod
    def _check_permissions(user, permission):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(permission):
            raise PermissionError("Unauthorized")


class Mutation(graphene.ObjectType):
    create_benefit_plan = CreateBenefitPlanMutation.Field()
    update_benefit_plan = UpdateBenefitPlanMutation.Field()
    delete_benefit_plan = DeleteBenefitPlanMutation.Field()

    create_beneficiary = CreateBeneficiaryMutation.Field()
    update_beneficiary = UpdateBeneficiaryMutation.Field()
    delete_beneficiary = DeleteBeneficiaryMutation.Field()
