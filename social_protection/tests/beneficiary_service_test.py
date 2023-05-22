import copy

from django.test import TestCase

from individual.models import Individual
from individual.tests.data import service_add_payload as service_add_individual_payload

from social_protection.models import Beneficiary, BenefitPlan
from social_protection.services import BeneficiaryService
from social_protection.tests.data import (
    service_beneficiary_add_payload,
    service_beneficiary_update_payload
)
from social_protection.tests.helpers import LogInHelper


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
        cls.benefit_plan = cls.__create_benefit_plan()
        cls.individual = cls.__create_individual()

    def test_add_benefitiary(self):
        result = self.service.create(service_beneficiary_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_update_benefit_plan(self):
        result = self.service.create(service_beneficiary_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        update_payload = copy.deepcopy(service_beneficiary_update_payload)
        update_payload['id'] = uuid
        result = self.service.update(service_beneficiary_update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().first_name, update_payload.get('first_name'))

    def test_delete_benefit_plan(self):
        result = self.service.create(service_beneficiary_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)

    @classmethod
    def __create_benefit_plan(cls):
        object_data = {
            **service_beneficiary_add_payload
        }

        benefit_plan = BenefitPlan(**object_data)
        benefit_plan.save(username=cls.user.username)

        return benefit_plan

    @classmethod
    def __create_individual(cls):
        object_data = {
            **service_add_individual_payload
        }

        individual = Individual(**object_data)
        individual.save(username=cls.user.username)

        return individual
