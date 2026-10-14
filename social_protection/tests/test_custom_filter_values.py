from django.test import TestCase

from core.test_helpers import create_test_interactive_user
from social_protection.custom_filters import BenefitPlanCustomFilterWizard
from social_protection.models import Beneficiary, BeneficiaryStatus
from social_protection.tests.test_helpers import create_benefit_plan, create_individual


class BenefitPlanCustomFilterStringValueTest(TestCase):
    """A string criterion selects the same beneficiaries whether its value is bare or JSON-quoted."""

    @classmethod
    def setUpTestData(cls):
        user = create_test_interactive_user(username="sp_cf_string_admin")
        plan = create_benefit_plan(user.username)
        cls.match = cls._beneficiary(user, plan, 'UAT release 26.10')
        cls.other = cls._beneficiary(user, plan, 'Other source')

    @staticmethod
    def _beneficiary(user, plan, source):
        beneficiary = Beneficiary(
            individual=create_individual(user.username),
            benefit_plan=plan,
            status=BeneficiaryStatus.POTENTIAL,
            json_ext={'source': source},
        )
        beneficiary.save(username=user.username)
        return beneficiary

    def _filter(self, criterion):
        queryset = Beneficiary.objects.filter(id__in=[self.match.id, self.other.id])
        return list(BenefitPlanCustomFilterWizard().apply_filter_to_queryset([criterion], queryset)
                    .values_list('id', flat=True))

    def test_bare_value(self):
        # Payment plan criteria send the value without quotes.
        for criterion in (
            'source__iexact__string=UAT release 26.10',
            'source__istartswith__string=UAT',
            'source__istartswith__string=U',
            'source__icontains__string=release',
        ):
            with self.subTest(criterion=criterion):
                self.assertEqual(self._filter(criterion), [self.match.id])

    def test_quoted_value(self):
        # Searchers send the value JSON-encoded.
        for criterion in (
            'source__iexact__string="UAT release 26.10"',
            'source__istartswith__string="UAT"',
            'source__icontains__string="release"',
        ):
            with self.subTest(criterion=criterion):
                self.assertEqual(self._filter(criterion), [self.match.id])

    def test_stored_criterion(self):
        # Eligibility criteria are stored in BenefitPlan.json_ext as dicts with a bare value.
        for filter_name, value in (('iexact', 'UAT release 26.10'), ('istartswith', 'UAT')):
            with self.subTest(filter=filter_name):
                criterion = {'field': 'source', 'filter': filter_name, 'type': 'string', 'value': value}
                self.assertEqual(self._filter(criterion), [self.match.id])
