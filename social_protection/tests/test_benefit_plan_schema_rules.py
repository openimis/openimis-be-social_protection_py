import copy
import json
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from core.test_helpers import LogInHelper
from individual.schema_usage import schema_usages
from individual.tests.test_helpers import set_individual_schema
from social_protection.custom_filters import BenefitPlanCustomFilterWizard
from social_protection.models import BenefitPlan
from social_protection.services import BenefitPlanService
from social_protection.tests.data import service_add_payload

STRING = {"type": "string"}


class BenefitPlanSchemaRulesTest(TestCase):
    user = None
    service = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = BenefitPlanService(cls.user)

    def setUp(self):
        super().setUp()
        set_individual_schema(self, {"properties": {
            "email": STRING,
            "household_size": {"type": "integer"},
            "income": {"type": "decimal"},
        }})

    def _create(self, properties, code='PLAN_S'):
        payload = copy.deepcopy(service_add_payload)
        payload.update(
            code=code, name=code,
            beneficiary_data_schema={"properties": properties},
        )
        return self.service.create(payload)

    @staticmethod
    def _update_payload(plan, properties, name=None):
        return {
            'id': plan.id, 'code': plan.code, 'name': name or plan.name,
            'beneficiary_data_schema': {"properties": properties},
        }

    def test_fields_missing_from_the_individual_schema_are_rejected(self):
        result = self._create({"email": STRING, "badge": STRING})
        self.assertFalse(result.get('success', True))
        self.assertIn('badge', result.get('detail', ''))
        self.assertFalse(BenefitPlan.objects.filter(code='PLAN_S').exists())

    def test_a_type_differing_from_the_individual_schema_is_rejected(self):
        result = self._create({"household_size": STRING})
        self.assertFalse(result.get('success', True))
        self.assertIn('household_size', result.get('detail', ''))

    def test_picked_fields_with_their_own_options_are_accepted(self):
        result = self._create({
            "email": {"type": "string", "uniqueness": True},
            "income": {
                "type": "decimal",
                "validationCalculation": {"name": "income_check"},
            },
        })
        self.assertTrue(result.get('success'), result)

    def test_an_older_plan_updates_while_its_schema_is_untouched(self):
        set_individual_schema(self, {"properties": {"badge": STRING}})
        created = self._create({"badge": STRING})
        self.assertTrue(created.get('success'), created)
        set_individual_schema(self, {"properties": {"email": STRING}})
        plan = BenefitPlan.objects.get(code='PLAN_S')

        untouched = self.service.update(self._update_payload(
            plan, name='Renamed', properties={"badge": STRING}))
        self.assertTrue(untouched.get('success'), untouched)

        edited = self.service.update(self._update_payload(
            plan, properties={"badge": STRING, "email": STRING}))
        self.assertFalse(edited.get('success', True))
        self.assertIn('badge', edited.get('detail', ''))

    def test_an_older_plan_stored_as_a_json_string_stays_editable(self):
        set_individual_schema(self, {"properties": {"badge": STRING}})
        self.assertTrue(self._create({"badge": STRING}).get('success'))
        set_individual_schema(self, {"properties": {"email": STRING}})
        BenefitPlan.objects.filter(code='PLAN_S').update(
            beneficiary_data_schema=json.dumps(
                {"properties": {"badge": STRING}}))
        plan = BenefitPlan.objects.get(code='PLAN_S')

        result = self.service.update(self._update_payload(
            plan, name='Renamed', properties={"badge": STRING}))

        self.assertTrue(result.get('success'), result)

    def test_field_options_follow_the_individual_schema_rules(self):
        result = self._create(
            {"email": {"type": "string", "uniqueness": False}})
        self.assertFalse(result.get('success', True))
        self.assertIn('email', result.get('detail', ''))

    def test_plans_deleted_or_not_hold_their_fields(self):
        self.assertTrue(
            self._create({"email": STRING}, code='PLAN_A').get('success'))
        self.assertTrue(
            self._create({"email": STRING}, code='PLAN_B').get('success'))
        self.service.delete(
            {'id': BenefitPlan.objects.get(code='PLAN_B').id})

        usages = schema_usages({'email', 'income'})

        self.assertIn(('PLAN_A', 'email'), usages)
        self.assertIn(('PLAN_B', 'email'), usages)

    def test_check_command_lists_plans_not_aligned_with_the_schema(self):
        set_individual_schema(
            self, {"properties": {"badge": STRING, "email": STRING}})
        self.assertTrue(
            self._create({"badge": STRING}, code='PLAN_OLD').get('success'))
        self.assertTrue(
            self._create({"email": STRING}, code='PLAN_OK').get('success'))
        set_individual_schema(self, {"properties": {"email": STRING}})
        out = StringIO()

        with self.assertRaises(CommandError):
            call_command('check_individual_schema_usage', stdout=out)

        self.assertIn('PLAN_OLD: ', out.getvalue())
        self.assertIn('badge', out.getvalue())
        self.assertNotIn('PLAN_OK', out.getvalue())


class BenefitPlanFilterValueTypesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = LogInHelper().get_or_create_user_api()

    def setUp(self):
        super().setUp()
        service = BenefitPlanService(self.user)
        for code, income, registered_on in [
            ('PLAN_LOW', 10.5, '2020-01-15'), ('PLAN_HI', 99.9, '2024-06-01'),
        ]:
            payload = copy.deepcopy(service_add_payload)
            payload.update(code=code, name=code, json_ext={
                'income': income, 'registered_on': registered_on})
            self.assertTrue(service.create(payload).get('success'))

    def _codes(self, *custom_filters):
        query = BenefitPlan.objects.filter(code__in=['PLAN_LOW', 'PLAN_HI'])
        filtered = BenefitPlanCustomFilterWizard().apply_filter_to_queryset(
            list(custom_filters), query)
        return set(filtered.values_list('code', flat=True))

    def test_decimal_values_are_compared_as_numbers(self):
        self.assertEqual(self._codes('income__gt__decimal=50'), {'PLAN_HI'})
        self.assertEqual(
            self._codes('income__gt__decimal="50"'), {'PLAN_HI'})
        stored_criterion = {
            'field': 'income', 'filter': 'gt', 'type': 'decimal', 'value': 50}
        self.assertEqual(self._codes(stored_criterion), {'PLAN_HI'})

    def test_date_values_are_compared_in_date_order(self):
        self.assertEqual(
            self._codes('registered_on__lt__date=2021-01-01'), {'PLAN_LOW'})
        self.assertEqual(
            self._codes('registered_on__gte__date="2020-01-15"'),
            {'PLAN_LOW', 'PLAN_HI'})
