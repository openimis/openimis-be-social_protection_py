import graphene
import pandas as pd
import re

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from core.gql.export_mixin import ExportableQueryMixin

from django.utils.translation import gettext as _
from core.gql_queries import ValidationMessageGQLType
from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from core.custom_filters import CustomFilterWizardStorage
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
    BeneficiaryGQLType
)
from social_protection.models import (
    BenefitPlan,
    Beneficiary
)
from social_protection.validation import validate_bf_unique_code, validate_bf_unique_name, validate_json_schema
import graphene_django_optimizer as gql_optimizer


def patch_details(beneficiary_df: pd.DataFrame):
    # Transform extension to DF columns 
    df_unfolded = pd.json_normalize(beneficiary_df['json_ext'])
    # Merge unfolded DataFrame with the original DataFrame
    df_final = pd.concat([beneficiary_df, df_unfolded], axis=1)
    df_final = df_final.drop('json_ext', axis=1)
    return df_final

class Query(ExportableQueryMixin, graphene.ObjectType):
    export_patches = {
        'beneficiary': [
            patch_details
        ]
    }
    exportable_fields = ['beneficiary']

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
        client_mutation_id=graphene.String(),
        customFilters=graphene.List(of_type=graphene.String),
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
        if not info.context.user.has_perms(SocialProtectionConfig.gql_benefit_plan_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = validate_bf_unique_code(kwargs['bf_code'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_bf_name_validity(self, info, **kwargs):
        if not info.context.user.has_perms(SocialProtectionConfig.gql_benefit_plan_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = validate_bf_unique_name(kwargs['bf_name'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_bf_schema_validity(self, info, **kwargs):
        if not info.context.user.has_perms(SocialProtectionConfig.gql_benefit_plan_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = validate_json_schema(kwargs['bf_schema'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_benefit_plan(self, info, **kwargs):
        filters = append_validity_filter(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        Query._check_permissions(
            info.context.user,
            SocialProtectionConfig.gql_benefit_plan_search_perms
        )
        query = BenefitPlan.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    def resolve_beneficiary(self, info, **kwargs):
        filters = append_validity_filter(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        Query._check_permissions(
            info.context.user,
            SocialProtectionConfig.gql_beneficiary_search_perms
        )
        query = Beneficiary.objects.filter(*filters)

        custom_filters = kwargs.get("customFilters", None)
        if custom_filters:
            query = CustomFilterWizardStorage.apply_filter_to_queryset(custom_filters, query)
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
