import copy

from django.test import TestCase

from individual.models import Individual
from individual.tests.data import service_add_individual_payload

from social_protection.models import Beneficiary, BenefitPlan
from social_protection.services import BeneficiaryService
from social_protection.tests.data import (
    service_add_payload,
    service_beneficiary_add_payload,
    service_beneficiary_update_payload
)
from core.test_helpers import LogInHelper
from social_protection.tests.test_helpers import create_benefit_plan, create_individual


class BeneficiaryServiceTest(TestCase):
    user = None
    service = None
    query_all = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = BeneficiaryService(cls.user)
        cls.query_all = Beneficiary.objects.filter(is_deleted=False)
        cls.benefit_plan = create_benefit_plan(cls.user.username, payload_override={
            'code': 'SGQLTest',
            'type': "INDIVIDUAL"
        })
        cls.individual = create_individual(cls.user.username)
        cls.payload = {
            **service_beneficiary_add_payload,
            "individual_id": cls.individual.id,
            "benefit_plan_id": cls.benefit_plan.id
        }

    def test_add_beneficiary(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_update_beneficiary(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        update_payload = copy.deepcopy(service_beneficiary_update_payload)
        update_payload['id'] = uuid
        update_payload['individual_id'] = self.individual.id
        update_payload['benefit_plan_id'] = self.benefit_plan.id
        result = self.service.update(update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().status, update_payload.get('status'))

    def test_delete_beneficiary(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)
