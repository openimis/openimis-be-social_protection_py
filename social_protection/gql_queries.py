import graphene
from graphene_django import DjangoObjectType

from core import prefix_filterset, ExtendedConnection
from policyholder.gql import PolicyHolderGQLType
from individual.gql_queries import IndividualGQLType
from social_protection.models import Beneficiary, BenefitPlan


class BenefitPlanGQLType(DjangoObjectType):
    uuid = graphene.String(source='uuid')

    class Meta:
        model = BenefitPlan
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "code": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "name": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            "max_beneficiaries": ["exact", "lt", "lte", "gt", "gte"],
            **prefix_filterset("holder__", PolicyHolderGQLType._meta.filter_fields),

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }
        connection_class = ExtendedConnection
<<<<<<< HEAD


class BeneficiaryGQLType(DjangoObjectType):
    uuid = graphene.String(source='uuid')

    class Meta:
        model = Beneficiary
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "status": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            **prefix_filterset("individual__", IndividualGQLType._meta.filter_fields),
            **prefix_filterset("benefit_plan__", BenefitPlanGQLType._meta.filter_fields),
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }
        connection_class = ExtendedConnection
=======
>>>>>>> 16e5bef8f77612b91937f476ab023fceeb6d0511
