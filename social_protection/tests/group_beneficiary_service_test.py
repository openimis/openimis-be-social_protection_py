import copy

from django.test import TestCase

from individual.models import Group

from social_protection.models import BenefitPlan, GroupBeneficiary, GroupBeneficiaryProjectTimeEntry
from social_protection.services import GroupBeneficiaryService
from social_protection.tests.data import (
    service_beneficiary_add_payload, service_beneficiary_update_status_active_payload,
)
from core.test_helpers import LogInHelper
from social_protection.tests.test_helpers import (
    create_benefit_plan, create_group, create_project,
    create_group_with_individual, add_group_to_benefit_plan,
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
            'code': 'GMAX1',
            'type': "GROUP",
            'max_beneficiaries': 1
        })

        cls.benefit_plan_no_max = create_benefit_plan(cls.user.username, payload_override={
            'code': 'GNOMAX',
            'type': "GROUP",
            'max_beneficiaries': None
        })

        cls.group = create_group(cls.user.username)
        cls.group2 = create_group(cls.user.username)
        cls.group3 = create_group(cls.user.username)
    
    def add_beneficiary_return_result(self, group: Group, benefit_plan: BenefitPlan = None, status="POTENTIAL"):
        benefit_plan = benefit_plan or self.benefit_plan
        payload = {
            **service_beneficiary_add_payload,
            "group_id": group.id,
            "benefit_plan_id": benefit_plan.id,
            "status": status
        }
        result = self.service.create(payload)
        return result
        
    def add_beneficiary_return_uuid(self, group: Group, benefit_plan: BenefitPlan = None, status="POTENTIAL"):
        result = self.add_beneficiary_return_result(group, benefit_plan, status)
        self.assertTrue(result.get('success', False), result.get('detaul', "No details provided"))
        return result.get('data', {}).get('uuid', None)

    def check_beneficiary_exists(self, uuid, with_status):
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        if with_status:
            self.assertEqual(query.first().status, with_status)
        
    def check_active_beneficiaries_count_eq(self, count, benefit_plan, msg=None):
        active_beneficiaries = self.query_all.filter(benefit_plan_id=benefit_plan.id, status="ACTIVE").distinct()
        self.assertEqual(active_beneficiaries.count(), count, msg)

    def test_add_group_beneficiary(self):
        uuid = self.add_beneficiary_return_uuid(self.group, self.benefit_plan, status="POTENTIAL")
        self.check_beneficiary_exists(uuid, with_status="POTENTIAL")

        self.assertEqual(self.benefit_plan.max_beneficiaries, 1)

        uuid = self.add_beneficiary_return_uuid(self.group2, self.benefit_plan, status="ACTIVE")
        self.check_beneficiary_exists(uuid, with_status="ACTIVE")
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "One active beneficiary should have been added")

        result = self.add_beneficiary_return_result(self.group3, self.benefit_plan, status="ACTIVE")
        self.assertFalse(result.get('success', True), "Benefit plan's 'max active beneficiaries' was not enforced")
        self.assertEqual(self.query_all.filter(group__code=self.group3.code).count(), 0)
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "Second active beneficiary addition should have been blocked")
        
        self.assertEqual(self.benefit_plan_no_max.max_beneficiaries, None)

        for i, group in enumerate([self.group, self.group2]):
            uuid = self.add_beneficiary_return_uuid(group, self.benefit_plan_no_max, status="ACTIVE")
            self.check_beneficiary_exists(uuid, with_status="ACTIVE")
            self.check_active_beneficiaries_count_eq(i+1, self.benefit_plan_no_max, f"{i+1} beneficiaries should be added and active")

    def test_update_group_beneficiary(self):
        def create_and_update_to_active(group, benefit_plan):
            uuid = self.add_beneficiary_return_uuid(group, benefit_plan, status="POTENTIAL")
            update_payload = {
                **service_beneficiary_update_status_active_payload,
                'id': uuid,
                'group_id': group.id,
                'benefit_plan_id': benefit_plan.id
            }
            return self.service.update(update_payload), uuid
        
        self.assertEqual(self.benefit_plan.max_beneficiaries, 1)

        result, uuid = create_and_update_to_active(self.group, self.benefit_plan)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        self.check_beneficiary_exists(uuid, with_status="ACTIVE")
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "One active beneficiary should have been added")

        update_payload = {
            **service_beneficiary_update_status_active_payload,
            'id': uuid,
            'group_id': self.group.id,
            'benefit_plan_id': self.benefit_plan.id,
            'json_ext': {
                'email': 'foo.bar@example.com',
                'able_bodied': True,
                'number_of_children': 2,
            }
        }
        result = self.service.update(update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        self.check_beneficiary_exists(uuid, with_status="ACTIVE")
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "One active beneficiary should have been added")

        result, uuid = create_and_update_to_active(self.group2, self.benefit_plan)
        self.assertFalse(result.get('success', True), "Benefit plan's 'max active beneficiaries' was not enforced")
        self.check_beneficiary_exists(uuid, with_status="POTENTIAL")
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "Second active beneficiary update should have been blocked")

        self.assertEqual(self.benefit_plan_no_max.max_beneficiaries, None)

        for i, group in enumerate([self.group, self.group2]):
            result, uuid = create_and_update_to_active(group, self.benefit_plan_no_max)
            self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
            self.check_beneficiary_exists(uuid, with_status="ACTIVE")
            self.check_active_beneficiaries_count_eq(i+1, self.benefit_plan_no_max, f"{i+1} beneficiaries should be added and active")

    def test_delete_group_beneficiary(self):
        uuid = self.add_beneficiary_return_uuid(self.group)
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)

    def test_enroll_project(self):
        uuid1 = self.add_beneficiary_return_uuid(self.group, self.benefit_plan_no_max)
        uuid2 = self.add_beneficiary_return_uuid(self.group2, self.benefit_plan_no_max)

        project = create_project(
            'test enrollment project',
            self.benefit_plan,
            self.user.username,
        )

        payload = {
            'ids': [uuid1, uuid2],
            'project_id': str(project.id),
        }

        self.service.enroll_project(payload)

        # Check that both beneficiaries are enrolled into the test project
        beneficiaries = GroupBeneficiary.objects.filter(id__in=[uuid1, uuid2])
        self.assertEqual(beneficiaries.count(), 2)
        for beneficiary in beneficiaries:
            self.assertEqual(beneficiary.project_id, project.id)
            self.assertEqual(beneficiary.benefit_plan_id, self.benefit_plan_no_max.id)

        payload = {
            'ids': [uuid1],
            'project_id': str(project.id),
        }

        self.service.enroll_project(payload)

        # Check that only the first beneficiary is enrolled into the test project
        beneficiaries = GroupBeneficiary.objects.filter(project_id=project.id)
        self.assertEqual(beneficiaries.count(), 1)
        beneficiary = beneficiaries.first()
        self.assertEqual(str(beneficiary.id), uuid1)


class GroupBeneficiaryTimeEntryServiceTest(TestCase):
    """Test GroupBeneficiaryService.bulk_update_time_entries"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = LogInHelper().get_or_create_user_api()
        cls.benefit_plan = create_benefit_plan(cls.user.username, {
            'code': 'GRPTSVC',
            'type': "GROUP",
        })
        cls.project = create_project(
            'Test Group Service Project',
            cls.benefit_plan,
            cls.user.username,
        )
        cls.project.working_days = 15
        cls.project.save(user=cls.user)

        cls.individual1, cls.group1, _ = create_group_with_individual(cls.user.username)
        cls.individual2, cls.group2, _ = create_group_with_individual(cls.user.username)

        cls.service = GroupBeneficiaryService(cls.user)

        cls.group_beneficiary1_uuid = add_group_to_benefit_plan(
            cls.service,
            cls.group1,
            cls.benefit_plan,
            {'status': 'ACTIVE', 'project_id': cls.project.id}
        )
        cls.group_beneficiary1 = GroupBeneficiary.objects.get(id=cls.group_beneficiary1_uuid)

        cls.group_beneficiary2_uuid = add_group_to_benefit_plan(
            cls.service,
            cls.group2,
            cls.benefit_plan,
            {'status': 'ACTIVE', 'project_id': cls.project.id}
        )
        cls.group_beneficiary2 = GroupBeneficiary.objects.get(id=cls.group_beneficiary2_uuid)

    def test_create_group_time_entries(self):
        obj_data = {
            'project_id': self.project.id,
            'time_entries': [
                {
                    'group_beneficiary_id': self.group_beneficiary1.id,
                    'day_number': 1,
                    'percent_complete': 60,
                },
                {
                    'group_beneficiary_id': self.group_beneficiary2.id,
                    'day_number': 1,
                    'percent_complete': 80,
                },
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['created'], 2)
        self.assertEqual(result['data']['updated'], 0)

        entries = GroupBeneficiaryProjectTimeEntry.objects.filter(
            group_beneficiary_id__in=[self.group_beneficiary1.id, self.group_beneficiary2.id],
            is_deleted=False
        )
        self.assertEqual(entries.count(), 2)

    def test_update_group_time_entries(self):
        entry1 = GroupBeneficiaryProjectTimeEntry(
            group_beneficiary_id=self.group_beneficiary1.id,
            day_number=2,
            percent_complete=20,
        )
        entry1.save(user=self.user)

        original_version = entry1.version
        original_date_valid_from = entry1.date_valid_from
        original_date_valid_to = entry1.date_valid_to
        self.assertEqual(original_version, 1)
        self.assertIsNotNone(original_date_valid_from)
        self.assertIsNone(original_date_valid_to)

        obj_data = {
            'project_id': self.project.id,
            'time_entries': [
                {
                    'id': entry1.id,
                    'group_beneficiary_id': self.group_beneficiary1.id,
                    'day_number': 2,
                    'percent_complete': 85,
                },
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['created'], 0)
        self.assertEqual(result['data']['updated'], 1)

        entry1.refresh_from_db()
        self.assertEqual(entry1.percent_complete, 85)

        # Check version incremented
        self.assertEqual(entry1.version, 2)

        # Check date_valid fields preserved
        self.assertEqual(entry1.date_valid_from, original_date_valid_from)
        self.assertEqual(entry1.date_valid_to, original_date_valid_to)

        # Check historical record created
        history = entry1.history.all()
        self.assertEqual(history.count(), 2)  # One for create, one for update
        latest_history = history.first()
        self.assertEqual(latest_history.percent_complete, 85)

    def test_invalid_group_beneficiary_id(self):
        import uuid
        obj_data = {
            'project_id': self.project.id,
            'time_entries': [
                {
                    'group_beneficiary_id': uuid.uuid4(),
                    'day_number': 1,
                    'percent_complete': 50,
                }
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertFalse(result['success'])
        self.assertIn('invalid', result['message'].lower())

    def test_day_number_validation(self):
        obj_data = {
            'project_id': self.project.id,
            'time_entries': [
                {
                    'group_beneficiary_id': self.group_beneficiary1.id,
                    'day_number': 0,
                    'percent_complete': 50,
                }
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertFalse(result['success'])
        self.assertIn('range', result['message'].lower())
