import copy

from django.test import TestCase

from social_protection.models import Group, BenefitPlan
from social_protection.services import GroupService
from social_protection.tests.data import (
    service_add_payload,
    service_group_add_payload,
    service_group_update_payload
)
from social_protection.tests.helpers import LogInHelper


class GroupServiceTest(TestCase):
    user = None
    service = None
    query_all = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = GroupService(cls.user)
        cls.query_all = Group.objects.filter(is_deleted=False)
        cls.benefit_plan = cls.__create_benefit_plan()
        cls.payload = {
            **service_group_add_payload,
            "benefit_plan_id": cls.benefit_plan.id,
        }

    def test_add_group(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_update_group(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        update_payload = copy.deepcopy(service_group_update_payload)
        update_payload['id'] = uuid
        update_payload['benefit_plan_id'] = self.benefit_plan.id
        result = self.service.update(update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().status, update_payload.get('status'))

    def test_delete_group(self):
        result = self.service.create(self.payload)
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
            **service_add_payload
        }

        benefit_plan = BenefitPlan(**object_data)
        benefit_plan.save(username=cls.user.username)

        return benefit_plan
