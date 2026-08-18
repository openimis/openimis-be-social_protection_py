import json
import uuid

from core.models import User
from core.models.openimis_graphql_test_case import BaseTestContext
from core.test_helpers import create_test_interactive_user, create_test_role
from social_protection.tests.test_helpers import (
    PatchedOpenIMISGraphQLTestCase,
    create_benefit_plan,
)


class BenefitPlanGQLTest(PatchedOpenIMISGraphQLTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.filter(
            username='Admin', i_user__isnull=False
        ).first()
        if not cls.user:
            cls.user = create_test_interactive_user(username='Admin')
        cls.user_token = BaseTestContext(user=cls.user).get_jwt()

        cls.test_officer = create_test_interactive_user(
            username="bpUserNoRight", roles=[create_test_role().id]
        )
        cls.test_officer_token = BaseTestContext(
            user=cls.test_officer
        ).get_jwt()

        cls.deleted_benefit_plan = create_benefit_plan(
            cls.user.username, payload_override={
                'code': 'BPDEL',
                'is_deleted': True,
            }
        )

    def test_undo_delete_benefit_plan_mutation_success(self):
        mutation = """
        mutation UndoDeleteBenefitPlan(
            $input: UndoDeleteBenefitPlanMutationInput!
        ) {
          undoDeleteBenefitPlan(input: $input) {
            clientMutationId
            internalId
          }
        }
        """

        variables = {
            "input": {
                "ids": [str(self.deleted_benefit_plan.id)],
                "clientMutationId": "undo_bp_123"
            }
        }

        response = self.query(
            mutation,
            variables=variables,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"}
        )

        self.assertResponseNoErrors(response)
        data = json.loads(response.content)['data']['undoDeleteBenefitPlan']
        self.assert_mutation_success(data['internalId'], self.user_token)

        self.deleted_benefit_plan.refresh_from_db()
        self.assertFalse(self.deleted_benefit_plan.is_deleted)

    def test_undo_delete_benefit_plan_mutation_requires_authentication(self):
        bp = create_benefit_plan(
            self.user.username, payload_override={
                'code': 'BPAUTH',
                'is_deleted': True,
            }
        )

        mutation = """
        mutation {
          undoDeleteBenefitPlan(input: {
            ids: ["%s"]
          }) {
            clientMutationId
            internalId
          }
        }
        """ % bp.id

        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = json.loads(response.content)['data']['undoDeleteBenefitPlan']
        self.assert_mutation_error(
            data['internalId'], self.user_token, 'authentication_required'
        )

        response = self.query(
            mutation,
            headers={
                "HTTP_AUTHORIZATION": f"Bearer {self.test_officer_token}"
            }
        )
        self.assertResponseNoErrors(response)
        data = json.loads(response.content)['data']['undoDeleteBenefitPlan']
        self.assert_mutation_error(
            data['internalId'], self.test_officer_token,
            'authentication_required'
        )

    def test_undo_delete_benefit_plan_mutation_invalid_ids(self):
        mutation = """
        mutation UndoDeleteBenefitPlan(
            $input: UndoDeleteBenefitPlanMutationInput!
        ) {
          undoDeleteBenefitPlan(input: $input) {
            clientMutationId
            internalId
          }
        }
        """

        variables = {
            "input": {
                "ids": [str(uuid.uuid4())],
                "clientMutationId": "undo_bp_bad"
            }
        }

        response = self.query(
            mutation,
            variables=variables,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"}
        )

        self.assertResponseNoErrors(response)
        data = json.loads(response.content)['data']['undoDeleteBenefitPlan']
        self.assert_mutation_error(
            data['internalId'], self.user_token, "does not exist"
        )
