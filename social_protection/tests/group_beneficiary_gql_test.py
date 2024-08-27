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
        create_group_with_individual, add_group_to_benefit_plan
from social_protection.services import GroupBeneficiaryService
import json

class GroupBeneficiaryGQLTest(openIMISGraphQLTestCase):
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
        cls.user_token = get_token(cls.user, cls.BaseTestContext(user=cls.user))
        cls.benefit_plan = create_benefit_plan(cls.user.username, payload_override={
            'code': 'GGQLTest',
            'type': 'GROUP'
        })
        cls.individual_2child, cls.group_2child, _ = create_group_with_individual(cls.user.username)
        cls.individual_1child, cls.group_1child, _ = create_group_with_individual(
            cls.user.username,
            individual_override={
                'first_name': 'OneChild',
                'json_ext': {
                    'number_of_children': 1
                }
            }
        )
        cls.individual, cls.group_0child, _ =  create_group_with_individual(
            cls.user.username,
            individual_override={
                'first_name': 'NoChild',
                'json_ext': {
                    'number_of_children': 0
                }
            }
        )
        cls.individual_not_enrolled, cls.group_not_enrolled, _ =  create_group_with_individual(
            cls.user.username,
            individual_override={
                'first_name': 'Not enrolled',
                'json_ext': {
                    'number_of_children': 0,
                    'able_bodied': True
                }
            }
        )
        cls.service = GroupBeneficiaryService(cls.user)
        add_group_to_benefit_plan(cls.service, cls.group_2child, cls.benefit_plan)
        add_group_to_benefit_plan(cls.service, cls.group_1child, cls.benefit_plan)
        add_group_to_benefit_plan(cls.service, cls.group_0child, cls.benefit_plan,
                                  payload_override={'status': 'ACTIVE'})

    def test_query_beneficiary_basic(self):
        response = self.query(
            f"""
            query {{
              groupBeneficiary(benefitPlan_Id: "{self.benefit_plan.uuid}", isDeleted: false, first: 10) {{
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
                    jsonExt
                    benefitPlan {{
                      id
                    }}
                    group {{
                      id
                      code
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
        beneficiary_data = response_data['data']['groupBeneficiary']
        self.assertEqual(beneficiary_data['totalCount'], 3)

        enrolled_group_codes = list(
            e['node']['group']['code'] for e in beneficiary_data['edges']
        )
        self.assertTrue(self.group_0child.code in enrolled_group_codes)
        self.assertTrue(self.group_1child.code in enrolled_group_codes)
        self.assertTrue(self.group_2child.code in enrolled_group_codes)
        self.assertFalse(self.group_not_enrolled.code in enrolled_group_codes)


    def test_query_beneficiary_custom_filter(self):
        query_str = f"""
            query {{
              groupBeneficiary(
                benefitPlan_Id: "{self.benefit_plan.uuid}",
                customFilters: ["number_of_children__lt__integer=2"],
                isDeleted: false,
                first: 10
              ) {{
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
                    jsonExt
                    benefitPlan {{
                      id
                    }}
                    group {{
                      id
                      code
                    }}
                    status
                  }}
                }}
              }}
            }}
        """
        response = self.query(query_str,
                              headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"})
        self.assertResponseNoErrors(response)
        response_data = json.loads(response.content)

        beneficiary_data = response_data['data']['groupBeneficiary']
        self.assertEqual(beneficiary_data['totalCount'], 2)

        returned_group_codes = list(
            e['node']['group']['code'] for e in beneficiary_data['edges']
        )
        self.assertTrue(self.group_0child.code in returned_group_codes)
        self.assertTrue(self.group_1child.code in returned_group_codes)
        self.assertFalse(self.group_2child.code in returned_group_codes)

        query_str = query_str.replace('__lt__', '__gte__')

        response = self.query(query_str,
                              headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"})
        self.assertResponseNoErrors(response)
        response_data = json.loads(response.content)

        beneficiary_data = response_data['data']['groupBeneficiary']
        self.assertEqual(beneficiary_data['totalCount'], 1)

        beneficiary_node = beneficiary_data['edges'][0]['node']
        group_data = beneficiary_node['group']
        self.assertEqual(group_data['code'], self.group_2child.code)


    def test_query_beneficiary_status_filter(self):
        query_str = f"""
            query {{
              groupBeneficiary(
                benefitPlan_Id: "{self.benefit_plan.uuid}",
                status: POTENTIAL,
                isDeleted: false,
                first: 10
              ) {{
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
                    jsonExt
                    benefitPlan {{
                      id
                    }}
                    group {{
                      id
                      code
                    }}
                    status
                  }}
                }}
              }}
            }}
        """
        response = self.query(query_str,
                              headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"})
        self.assertResponseNoErrors(response)
        response_data = json.loads(response.content)

        beneficiary_data = response_data['data']['groupBeneficiary']
        self.assertEqual(beneficiary_data['totalCount'], 2)

        enrolled_group_codes = list(
            e['node']['group']['code'] for e in beneficiary_data['edges']
        )
        self.assertFalse(self.group_0child.code in enrolled_group_codes)
        self.assertTrue(self.group_1child.code in enrolled_group_codes)
        self.assertTrue(self.group_2child.code in enrolled_group_codes)
        self.assertFalse(self.group_not_enrolled.code in enrolled_group_codes)

