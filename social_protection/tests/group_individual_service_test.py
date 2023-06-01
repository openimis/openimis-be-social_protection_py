import copy

from django.test import TestCase

from individual.models import Individual
from social_protection.models import GroupIndividual, Group, BenefitPlan
from social_protection.services import GroupIndividualService
from individual.tests.data import service_add_payload as service_add_individual_payload
from individual.tests.data import service_add_payload2 as service_add_individual_payload2
from social_protection.tests.data import (
    service_group_add_payload,
    service_group_update_payload, service_add_payload
)
from social_protection.tests.helpers import LogInHelper


class GroupIndividualServiceTest(TestCase):
    user = None
    service = None
    query_all = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = GroupIndividualService(cls.user)
        cls.query_all = GroupIndividual.objects.filter(is_deleted=False)
        cls.benefit_plan = cls.__create_benefit_plan()
        cls.group = cls.__create_group()
        cls.individual1 = cls.__create_individual(**service_add_individual_payload)
        cls.individual2 = cls.__create_individual(**service_add_individual_payload2)
        cls.payload = {
            "individual_id": cls.individual1.id,
            "group_id": cls.group.id,
        }

    def test_add_group_individual(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_update_group_individual(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        update_payload = {
            "id": uuid,
            "individual_id": self.individual2.id
        }
        result = self.service.update(update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().individual_id, update_payload.get('individual_id'))

    def test_delete_group_individual(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)

    @classmethod
    def __create_individual(cls, **individual_payload):
        object_data = {
            **individual_payload
        }

        individual = Individual(**object_data)
        individual.save(username=cls.user.username)

        return individual

    @classmethod
    def __create_benefit_plan(cls):
        object_data = {
            **service_add_payload
        }

        benefit_plan = BenefitPlan(**object_data)
        benefit_plan.save(username=cls.user.username)

        return benefit_plan

    @classmethod
    def __create_group(cls):
        object_data = {
            **service_group_add_payload,
            "benefit_plan_id": cls.benefit_plan.id
        }

        group = Group(**object_data)
        group.save(username=cls.user.username)

        return group
