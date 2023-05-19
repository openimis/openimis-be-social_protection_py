import graphene
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from django.utils.translation import gettext as _
from core.gql_queries import ValidationMessageGQLType
from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from social_protection.apps import SocialProtectionConfig
from social_protection.gql_mutations import CreateBenefitPlanMutation, UpdateBenefitPlanMutation, \
    DeleteBenefitPlanMutation
from social_protection.gql_queries import BenefitPlanGQLType
from social_protection.models import BenefitPlan
from social_protection.validation import check_bf_unique_code, check_bf_unique_name
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

    def resolve_bf_code_validity(self, info, **kwargs):
        if not info.context.user.has_perms(SocialProtectionConfig.gql_benefit_plan_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = check_bf_unique_code(kwargs['bf_code'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_bf_name_validity(self, info, **kwargs):
        if not info.context.user.has_perms(SocialProtectionConfig.gql_benefit_plan_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = check_bf_unique_name(kwargs['bf_code'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_benefit_plan(self, info, **kwargs):
        filters = append_validity_filter(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        Query._check_permissions(info.context.user)
        query = BenefitPlan.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    @staticmethod
    def _check_permissions(user):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                SocialProtectionConfig.gql_benefit_plan_search_perms):
            raise PermissionError("Unauthorized")


class Mutation(graphene.ObjectType):
    create_benefit_plan = CreateBenefitPlanMutation.Field()
    update_benefit_plan = UpdateBenefitPlanMutation.Field()
    delete_benefit_plan = DeleteBenefitPlanMutation.Field()
