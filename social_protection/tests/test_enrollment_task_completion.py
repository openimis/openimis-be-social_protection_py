"""
Completing an enrolment task enrols the individuals (or groups) frozen into its
upload at confirmation time. Two tasks confirmed for the same people before
either is approved must not enrol them twice.
"""
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from core.test_helpers import create_test_interactive_user
from individual.models import IndividualDataSource, IndividualDataSourceUpload
from social_protection.apps import SocialProtectionConfig
from social_protection.models import (
    Beneficiary, BeneficiaryStatus, BenefitPlan, BenefitPlanDataUploadRecords, GroupBeneficiary,
)
from social_protection.tests.test_helpers import (
    add_individual_to_group, create_group, create_group_with_individual, create_individual,
)
from tasks_management.apps import TasksManagementConfig
from tasks_management.models import Task
from tasks_management.services import TaskService


class EnrollmentTaskCompletionTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = create_test_interactive_user(username="sp_enr_dup_admin")
        cls.plan = BenefitPlan(code="ENRDUPI", name="Enrolment duplicate test",
                               type=BenefitPlan.BenefitPlanType.INDIVIDUAL_TYPE)
        cls.plan.save(username=cls.admin.username)
        cls.group_plan = BenefitPlan(code="ENRDUPG", name="Group enrolment duplicate test",
                                     type=BenefitPlan.BenefitPlanType.GROUP_TYPE)
        cls.group_plan.save(username=cls.admin.username)

    def _confirmed_task(self, plan, individuals, business_event):
        """An enrolment task as on_confirm_enrollment_of_individual creates it."""
        upload = IndividualDataSourceUpload(source_name='enr_dup', source_type='beneficiary import')
        upload.save(username=self.admin.username)
        record = BenefitPlanDataUploadRecords(data_upload=upload, benefit_plan=plan, workflow='Enrollment')
        record.save(username=self.admin.username)
        for individual in individuals:
            IndividualDataSource(upload=upload, individual=individual, json_ext=individual.json_ext,
                                 validations={}).save(username=self.admin.username)
        task = Task(
            source='import_valid_items', entity=record, status=Task.Status.ACCEPTED,
            executor_action_event=TasksManagementConfig.default_executor_event,
            business_event=business_event, business_status={}, data={},
            json_ext={'data_upload_id': str(upload.id), 'benefit_plan_id': str(plan.id),
                      'beneficiary_status': BeneficiaryStatus.POTENTIAL},
        )
        task.save(username=self.admin.username)
        return task

    def _complete(self, task):
        result = TaskService(self.admin).complete_task({'id': task.id})
        self.assertTrue(result.get('success'), result)

    def test_two_confirmed_tasks_enrol_each_individual_once(self):
        individuals = [create_individual(self.admin.username) for _ in range(2)]
        tasks = [self._confirmed_task(self.plan, individuals, SocialProtectionConfig.validation_enrollment)
                 for _ in range(2)]
        for task in tasks:
            self._complete(task)
        for individual in individuals:
            self.assertEqual(Beneficiary.objects.filter(
                individual=individual, benefit_plan=self.plan, is_deleted=False).count(), 1)

    def test_deleted_enrolment_does_not_block_a_new_one(self):
        individual = create_individual(self.admin.username)
        old = Beneficiary(individual=individual, benefit_plan=self.plan,
                          status=BeneficiaryStatus.POTENTIAL, json_ext={}, is_deleted=True)
        old.save(username=self.admin.username)
        self._complete(self._confirmed_task(self.plan, [individual], SocialProtectionConfig.validation_enrollment))
        self.assertEqual(Beneficiary.objects.filter(
            individual=individual, benefit_plan=self.plan, is_deleted=False).count(), 1)

    def test_two_confirmed_tasks_enrol_each_group_once(self):
        heads, groups = [], []
        for _ in range(2):
            head, group, _ = create_group_with_individual(self.admin.username)
            heads.append(head)
            groups.append(group)
        tasks = [self._confirmed_task(self.group_plan, heads, SocialProtectionConfig.validation_group_enrollment)
                 for _ in range(2)]
        for task in tasks:
            self._complete(task)
        for group in groups:
            self.assertEqual(GroupBeneficiary.objects.filter(
                group=group, benefit_plan=self.group_plan, is_deleted=False).count(), 1)

    def test_individual_listed_twice_in_one_upload_is_enrolled_once(self):
        individual = create_individual(self.admin.username)
        self._complete(self._confirmed_task(
            self.plan, [individual, individual], SocialProtectionConfig.validation_enrollment))
        self.assertEqual(Beneficiary.objects.filter(
            individual=individual, benefit_plan=self.plan, is_deleted=False).count(), 1)

    def test_group_enrolment_uses_the_active_head_membership(self):
        # The head left group B (enrolled) for group A: only the active membership counts.
        head, group_b, old_membership = create_group_with_individual(self.admin.username)
        GroupBeneficiary(group=group_b, benefit_plan=self.group_plan, status=BeneficiaryStatus.POTENTIAL,
                         json_ext={}).save(username=self.admin.username)
        old_membership.delete(username=self.admin.username)
        group_a = create_group(self.admin.username)
        add_individual_to_group(self.admin.username, head, group_a)
        self._complete(self._confirmed_task(
            self.group_plan, [head], SocialProtectionConfig.validation_group_enrollment))
        self.assertEqual(GroupBeneficiary.objects.filter(
            group=group_a, benefit_plan=self.group_plan, is_deleted=False).count(), 1)
        self.assertEqual(GroupBeneficiary.objects.filter(
            group=group_b, benefit_plan=self.group_plan, is_deleted=False).count(), 1)

    def test_group_enrolment_after_the_head_was_replaced(self):
        # Replacing a head keeps the former head's membership active, without role.
        former_head, group, membership = create_group_with_individual(self.admin.username)
        task = self._confirmed_task(self.group_plan, [former_head], SocialProtectionConfig.validation_group_enrollment)
        membership.role = None
        membership.save(username=self.admin.username)
        new_head = create_individual(self.admin.username, {'json_ext': {'marker': 'new head'}})
        add_individual_to_group(self.admin.username, new_head, group)
        self._complete(task)
        enrolment = GroupBeneficiary.objects.get(group=group, benefit_plan=self.group_plan, is_deleted=False)
        self.assertEqual(enrolment.json_ext, new_head.json_ext)

    def test_head_of_two_groups_is_not_resolved_to_either(self):
        head, group_a, _ = create_group_with_individual(self.admin.username)
        group_b = create_group(self.admin.username)
        add_individual_to_group(self.admin.username, head, group_b)
        with self.assertLogs('social_protection.signals.on_validation_import_valid_items', level='WARNING') as logs:
            self._complete(self._confirmed_task(
                self.group_plan, [head], SocialProtectionConfig.validation_group_enrollment))
        self.assertIn(str(head.id), '\n'.join(logs.output))
        self.assertFalse(GroupBeneficiary.objects.filter(
            group__in=[group_a, group_b], benefit_plan=self.group_plan).exists())

    def test_completion_locks_the_plan_row(self):
        individual = create_individual(self.admin.username)
        task = self._confirmed_task(self.plan, [individual], SocialProtectionConfig.validation_enrollment)
        with CaptureQueriesContext(connection) as queries:
            self._complete(task)
        self.assertTrue(any('FOR NO KEY UPDATE' in q['sql'] and 'social_protection_benefitplan' in q['sql']
                            for q in queries.captured_queries))

    def test_head_membership_is_preferred_over_another_role(self):
        head, group_a, _ = create_group_with_individual(self.admin.username)
        # Group B has its own head; the person is an ordinary member of it.
        _, group_b, _ = create_group_with_individual(self.admin.username)
        add_individual_to_group(self.admin.username, head, group_b, is_head=False)
        self._complete(self._confirmed_task(
            self.group_plan, [head], SocialProtectionConfig.validation_group_enrollment))
        self.assertTrue(GroupBeneficiary.objects.filter(group=group_a, benefit_plan=self.group_plan).exists())
        self.assertFalse(GroupBeneficiary.objects.filter(group=group_b, benefit_plan=self.group_plan).exists())

    def test_membership_created_after_confirmation_is_ignored(self):
        # The confirmed head left the group and heads a new one created afterwards.
        head, group_a, membership = create_group_with_individual(self.admin.username)
        task = self._confirmed_task(self.group_plan, [head], SocialProtectionConfig.validation_group_enrollment)
        membership.delete(username=self.admin.username)
        group_c = create_group(self.admin.username)
        add_individual_to_group(self.admin.username, head, group_c)
        with self.assertLogs('social_protection.signals.on_validation_import_valid_items', level='WARNING'):
            self._complete(task)
        self.assertFalse(GroupBeneficiary.objects.filter(
            group__in=[group_a, group_c], benefit_plan=self.group_plan).exists())
