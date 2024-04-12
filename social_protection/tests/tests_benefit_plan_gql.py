

import uuid
from dataclasses import dataclass

from core.models import User
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase
from core.test_helpers import create_test_interactive_user
from graphql_jwt.shortcuts import get_token

# from openIMIS import schema


@dataclass
class DummyContext:
    """ Just because we need a context to generate. """
    user: User





    
class BenefitPlanGQLTestCase(openIMISGraphQLTestCase):
    admin_user = None
    admin_token = None
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(username="testLocationAdmin")
        cls.admin_token = get_token(cls.admin_user, DummyContext(user=cls.admin_user))
 
        
        
    def test_create_benefit_plan_test(self):
        input_param = f"""\
            code: "T_GQL"\
            name: "test GQL"\
            type: INDIVIDUAL\
            dateValidFrom: "2024-04-01"\
            dateValidTo: "2024-04-30"\
            clientMutationId: "{str(uuid.uuid4())}" """
        
        content=self.send_mutation("createBenefitPlan", input_param, self.admin_token , raw = True)        

    