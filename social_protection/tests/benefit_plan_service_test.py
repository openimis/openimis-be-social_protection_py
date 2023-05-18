import copy

from django.test import TestCase

from social_protection.models import BenefitPlan
from social_protection.services import BenefitPlanService
from social_protection.tests.data import (
    service_add_payload,
    service_add_payload_no_ext,
    service_update_payload
)
from social_protection.tests.helpers import LogInHelper


class BenefitPlanServiceTest(TestCase):
    user = None
    service = None
    query_all = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = BenefitPlanService(cls.user)
        cls.query_all = BenefitPlan.objects.filter(is_deleted=False)

    def test_add_benefit_plan(self):
        result = self.service.create(service_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_add_benefit_plan_no_ext(self):
        result = self.service.create(service_add_payload_no_ext)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_update_individual(self):
        result = self.service.create(service_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        update_payload = copy.deepcopy(service_update_payload)
        update_payload['id'] = uuid
        result = self.service.update(update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().first_name, update_payload.get('first_name'))

    def test_delete_individual(self):
        result = self.service.create(service_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)
