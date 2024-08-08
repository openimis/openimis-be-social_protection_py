import base64
from unittest import mock
import graphene
from core.models import User
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase
from core.test_helpers import create_test_interactive_user
from social_protection import schema as sp_schema
from graphene import Schema
from graphene.test import Client
from graphene_django.utils.testing import GraphQLTestCase
from django.conf import settings
from graphql_jwt.shortcuts import get_token
from social_protection.tests.test_helpers import create_benefit_plan,\
        create_individual, add_individual_to_benefit_plan
from social_protection.services import BeneficiaryService
import json

class SocialProtectionGQLTest(openIMISGraphQLTestCase):
    schema = Schema(query=sp_schema.Query)

    class BaseTestContext:
        def __init__(self, user):
            self.user = user

    class AnonymousUserContext:
        user = mock.Mock(is_anonymous=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.filter(username='admin', i_user__isnull=False).first()
        if not cls.user:
            cls.user=create_test_interactive_user(username='admin')
        # some test data so as to created contract properly
        cls.user_token = get_token(cls.user, cls.BaseTestContext(user=cls.user))
        cls.benefit_plan = create_benefit_plan(cls.user.username)
        cls.individual = create_individual(cls.user.username)
        cls.service = BeneficiaryService(cls.user)
        add_individual_to_benefit_plan(cls.service, cls.individual, cls.benefit_plan)

    def test_query_beneficiary_basic(self):
        response = self.query(
            f"""
            query {{
              beneficiary(benefitPlan_Id: "{self.benefit_plan.uuid}", isDeleted: false, first: 10) {{
                totalCount
                pageInfo {{
                  hasNextPage
                  hasPreviousPage
                  startCursor
                  endCursor
                }}
                edges {{
                  node {{
                    id
                    benefitPlan {{
                      id
                    }}
                    individual {{
                      firstName
                      lastName
                      dob
                    }}
                    status
                  }}
                }}
              }}
            }}
            """
        , headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"})
        self.assertResponseNoErrors(response)
        response_data = json.loads(response.content)

        # Asserting the response has one beneficiary record
        beneficiary_data = response_data['data']['beneficiary']
        self.assertEqual(beneficiary_data['totalCount'], 1)

        # Asserting it matches the expected individual
        beneficiary_node = beneficiary_data['edges'][0]['node']
        individual_data = beneficiary_node['individual']
        self.assertEqual(individual_data['firstName'], self.individual.first_name)
        self.assertEqual(individual_data['lastName'], self.individual.last_name)
        self.assertEqual(individual_data['dob'], self.individual.dob.strftime('%Y-%m-%d'))

