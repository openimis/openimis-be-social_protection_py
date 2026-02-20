import copy
import uuid

from django.test import TestCase

from individual.models import Individual

from social_protection.models import Beneficiary, BenefitPlan, BeneficiaryProjectTimeEntry
from social_protection.services import BeneficiaryService
from social_protection.tests.data import (
    service_beneficiary_add_payload,
    service_beneficiary_update_status_active_payload
)
from core.test_helpers import LogInHelper
from social_protection.tests.test_helpers import (
    create_benefit_plan,
    create_individual,
    create_project,
    add_individual_to_benefit_plan,
)


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
            'code': 'IMAX1',
            'type': "INDIVIDUAL",
            'max_beneficiaries': 1
        })

        cls.benefit_plan_no_max = create_benefit_plan(cls.user.username, payload_override={
            'code': 'INOMAX',
            'type': "INDIVIDUAL",
            'max_beneficiaries': None
        })

        cls.individual = create_individual(cls.user.username)
        cls.individual2 = create_individual(cls.user.username, payload_override={
            'first_name': "Second"
        })
        cls.individual3 = create_individual(cls.user.username, payload_override={
            'first_name': "Third"
        })

    def add_beneficiary_return_result(self, individual: Individual, benefit_plan: BenefitPlan = None, status="POTENTIAL"):
        benefit_plan = benefit_plan or self.benefit_plan
        payload = {
            **service_beneficiary_add_payload,
            "individual_id": individual.id,
            "benefit_plan_id": benefit_plan.id,
            "status": status
        }
        result = self.service.create(payload)
        return result

    def add_beneficiary_return_uuid(self, individual: Individual, benefit_plan: BenefitPlan = None, status="POTENTIAL"):
        result = self.add_beneficiary_return_result(individual, benefit_plan, status)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        return result.get('data', {}).get('uuid')

    def check_beneficiary_exists(self, uuid, with_status=None):
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        if with_status:
            self.assertEqual(query.first().status, with_status)

    def check_active_beneficiaries_count_eq(self, count, benefit_plan, msg=None):
        active_beneficiaries = self.query_all.filter(benefit_plan_id=benefit_plan.id, status="ACTIVE").distinct()
        self.assertEqual(active_beneficiaries.count(), count, msg)

    def test_add_beneficiary(self):
        uuid = self.add_beneficiary_return_uuid(self.individual, self.benefit_plan, status="POTENTIAL")
        self.check_beneficiary_exists(uuid, with_status="POTENTIAL")

        self.assertEqual(self.benefit_plan.max_beneficiaries, 1)

        uuid = self.add_beneficiary_return_uuid(self.individual2, self.benefit_plan, status="ACTIVE")
        self.check_beneficiary_exists(uuid, with_status="ACTIVE")
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "One active beneficiary should have been added")

        result = self.add_beneficiary_return_result(self.individual3, self.benefit_plan, status="ACTIVE")
        self.assertFalse(result.get('success', True), "Benefit plan's 'max active beneficiaries' was not enforced")
        self.assertEqual(self.query_all.filter(individual__first_name=self.individual3.first_name).count(), 0)
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "Second active beneficiary creation should have been blocked")

        self.assertEqual(self.benefit_plan_no_max.max_beneficiaries, None)

        for i, individual in enumerate([self.individual, self.individual2]):
            uuid = self.add_beneficiary_return_uuid(individual, self.benefit_plan_no_max, status="ACTIVE")
            self.check_beneficiary_exists(uuid, with_status="ACTIVE")
            self.check_active_beneficiaries_count_eq(i + 1, self.benefit_plan_no_max, f"{i + 1} beneficiaries should be added and active")

    def test_update_beneficiary(self):
        def create_and_update_to_active(individual, benefit_plan):
            uuid = self.add_beneficiary_return_uuid(individual, benefit_plan)
            update_payload = {
                **service_beneficiary_update_status_active_payload,
                'id': uuid,
                'individual_id': individual.id,
                'benefit_plan_id': benefit_plan.id
            }
            return self.service.update(update_payload), uuid

        self.assertEqual(self.benefit_plan.max_beneficiaries, 1)

        result, uuid = create_and_update_to_active(self.individual, self.benefit_plan)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        self.check_beneficiary_exists(uuid, with_status="ACTIVE")
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "One active beneficiary should have been added")

        result, uuid = create_and_update_to_active(self.individual, self.benefit_plan)
        self.assertFalse(result.get('success', True), "Benefit plan's 'max active beneficiaries' was not enforced")
        self.check_beneficiary_exists(uuid, with_status="POTENTIAL")
        self.check_active_beneficiaries_count_eq(1, self.benefit_plan, "Second active beneficiary update should have been blocked")

        self.assertEqual(self.benefit_plan_no_max.max_beneficiaries, None)

        for i, individual in enumerate([self.individual, self.individual2]):
            result, uuid = create_and_update_to_active(individual, self.benefit_plan_no_max)
            self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
            self.check_beneficiary_exists(uuid, "ACTIVE")
            self.check_active_beneficiaries_count_eq(i + 1, self.benefit_plan_no_max, f"{i + 1} beneficiaries should be added and active")

    def test_delete_beneficiary(self):
        uuid = self.add_beneficiary_return_uuid(self.individual)
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)

    def test_enroll_project(self):
        uuid1 = self.add_beneficiary_return_uuid(self.individual, self.benefit_plan_no_max)
        uuid2 = self.add_beneficiary_return_uuid(self.individual2, self.benefit_plan_no_max)

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
        beneficiaries = Beneficiary.objects.filter(id__in=[uuid1, uuid2])
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
        beneficiaries = Beneficiary.objects.filter(project_id=project.id)
        self.assertEqual(beneficiaries.count(), 1)
        beneficiary = beneficiaries.first()
        self.assertEqual(str(beneficiary.id), uuid1)


class BeneficiaryTimeEntryServiceTest(TestCase):
    """Test BeneficiaryService.bulk_update_time_entries"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = LogInHelper().get_or_create_user_api()
        cls.benefit_plan = create_benefit_plan(cls.user.username, {
            'code': 'BENTSVC',
            'type': "INDIVIDUAL",
        })
        cls.project = create_project(
            'Test Service Project',
            cls.benefit_plan,
            cls.user.username,
        )
        cls.project.working_days = 10
        cls.project.save(user=cls.user)

        cls.individual1 = create_individual(cls.user.username, {'first_name': 'Alice'})
        cls.individual2 = create_individual(cls.user.username, {'first_name': 'Bob'})

        cls.service = BeneficiaryService(cls.user)

        cls.beneficiary1_uuid = add_individual_to_benefit_plan(
            cls.service,
            cls.individual1,
            cls.benefit_plan,
            {'status': 'ACTIVE'}
        )
        cls.beneficiary1 = Beneficiary.objects.get(id=cls.beneficiary1_uuid)
        cls.beneficiary1.project = cls.project
        cls.beneficiary1.save(user=cls.user)

        cls.beneficiary2_uuid = add_individual_to_benefit_plan(
            cls.service,
            cls.individual2,
            cls.benefit_plan,
            {'status': 'ACTIVE'}
        )
        cls.beneficiary2 = Beneficiary.objects.get(id=cls.beneficiary2_uuid)
        cls.beneficiary2.project = cls.project
        cls.beneficiary2.save(user=cls.user)



    def test_create_time_entries(self):
        obj_data = {
            'project_id': self.project.id,
            'time_entries': [
                {
                    'beneficiary_id': self.beneficiary1.id,
                    'day_number': 1,
                    'percent_complete': 50,
                },
                {
                    'beneficiary_id': self.beneficiary2.id,
                    'day_number': 1,
                    'percent_complete': 75,
                },
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['created'], 2)
        self.assertEqual(result['data']['updated'], 0)

        entries = BeneficiaryProjectTimeEntry.objects.filter(
            beneficiary_id__in=[self.beneficiary1.id, self.beneficiary2.id],
            is_deleted=False
        )
        self.assertEqual(entries.count(), 2)

    def test_update_time_entries(self):
        entry1 = BeneficiaryProjectTimeEntry(
            beneficiary_id=self.beneficiary1.id,
            day_number=2,
            percent_complete=30,
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
                    'beneficiary_id': self.beneficiary1.id,
                    'day_number': 2,
                    'percent_complete': 90,
                },
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['created'], 0)
        self.assertEqual(result['data']['updated'], 1)

        entry1.refresh_from_db()
        self.assertEqual(entry1.percent_complete, 90)

        # Check version incremented
        self.assertEqual(entry1.version, 2)

        # Check date_valid fields preserved
        self.assertEqual(entry1.date_valid_from, original_date_valid_from)
        self.assertEqual(entry1.date_valid_to, original_date_valid_to)

        # Check historical record created
        history = entry1.history.all()
        self.assertEqual(history.count(), 2)  # One for create, one for update
        latest_history = history.first()
        self.assertEqual(latest_history.percent_complete, 90)

    def test_invalid_project_id(self):
        obj_data = {
            'project_id': uuid.uuid4(),
            'time_entries': [
                {
                    'beneficiary_id': self.beneficiary1.id,
                    'day_number': 5,
                    'percent_complete': 50,
                }
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertFalse(result['success'])
        self.assertIn('Project not found', result['detail'])

    def test_invalid_beneficiary_id(self):
        obj_data = {
            'project_id': self.project.id,
            'time_entries': [
                {
                    'beneficiary_id': uuid.uuid4(),
                    'day_number': 1,
                    'percent_complete': 50,
                }
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertFalse(result['success'])
        self.assertIn('Invalid beneficiary IDs', result['detail'])

    def test_day_number_out_of_range(self):
        obj_data = {
            'project_id': self.project.id,
            'time_entries': [
                {
                    'beneficiary_id': self.beneficiary1.id,
                    'day_number': 999,
                    'percent_complete': 50,
                }
            ]
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertFalse(result['success'])
        self.assertIn('Day number must be between 1 and 10.', result['detail'])

    def test_empty_time_entries(self):
        obj_data = {
            'project_id': self.project.id,
            'time_entries': []
        }

        result = self.service.bulk_update_time_entries(obj_data)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['created'], 0)
        self.assertEqual(result['data']['updated'], 0)
