"""get_queryset honours the OP-2029 validity contract (epic OP-3317, phase 1).

Explicit validity values return the expected rows; a caller asking for
nothing gets what it got before the contract existed.
"""

from django.test import TestCase

from core.test_helpers import assert_row_filters, create_test_interactive_user, mark_deleted
from social_protection.models import Beneficiary, BeneficiaryStatus
from social_protection.tests.test_helpers import create_benefit_plan, create_individual


class BeneficiaryRowFiltersTest(TestCase):
    def test_beneficiary(self):
        user = create_test_interactive_user(username="benrowfilters")
        plan = create_benefit_plan(user.username)

        def beneficiary():
            row = Beneficiary(
                individual=create_individual(user.username), benefit_plan=plan,
                status=BeneficiaryStatus.POTENTIAL, json_ext={},
            )
            row.save(username=user.username)
            return row

        live = beneficiary()
        deleted = mark_deleted(beneficiary())
        assert_row_filters(
            self, Beneficiary, Beneficiary.objects.filter(id__in=[live.id, deleted.id]), user,
            live.id, deleted.id, default_hides_deleted=False,
        )
