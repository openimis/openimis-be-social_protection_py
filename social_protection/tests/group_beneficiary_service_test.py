import copy

from django.test import TestCase

from individual.models import Group

from social_protection.models import BenefitPlan, GroupBeneficiary
from social_protection.services import GroupBeneficiaryService
from social_protection.tests.data import (
    service_beneficiary_add_payload, service_beneficiary_update_payload,
)
from core.test_helpers import LogInHelper
from social_protection.tests.test_helpers import (
    create_benefit_plan, create_group
)
from datetime import datetime


class GroupBeneficiaryServiceTest(TestCase):
    user = None
    service = None
    query_all = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = GroupBeneficiaryService(cls.user)
        cls.query_all = GroupBeneficiary.objects.filter(is_deleted=False)
        cls.benefit_plan = create_benefit_plan(cls.user.username, payload_override={
            'type': "GROUP"
        })
        cls.group = create_group(cls.user.username)
        cls.payload = {
            **service_beneficiary_add_payload,
            "group_id": cls.group.id,
            "benefit_plan_id": cls.benefit_plan.id,
        }

    def test_add_group_beneficiary(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_update_group_beneficiary(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        update_payload = copy.deepcopy(service_beneficiary_update_payload)
        update_payload['id'] = uuid
        update_payload['group_id'] = self.group.id
        update_payload['benefit_plan_id'] = self.benefit_plan.id
        result = self.service.update(update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().status, update_payload.get('status'))

    def test_delete_group_beneficiary(self):
        result = self.service.create(self.payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)
