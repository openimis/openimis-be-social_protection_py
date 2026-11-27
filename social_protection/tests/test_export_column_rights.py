"""
OP-3353 / CVE-2026-82491: beneficiary export columns may only follow relations the caller
is allowed to read.

The export mixin of this module (`ExportableSocialProtectionQueryMixin`) handed the
requested columns straight to ``values_list``. A user holding only the beneficiary search
right could export ``group.code`` without the group search right, and anyone could export
the password hash of a record's creator. The check lives in
`core.models.ExportableQueryModel.create_csv_export`, which this mixin calls; these tests
go through GraphQL and read the file the export wrote.
"""

import json

from core.models import ExportableQueryModel
from core.models.openimis_graphql_test_case import (
    BaseTestContext,
    openIMISGraphQLTestCase,
)
from core.test_helpers import (
    create_admin_role,
    create_right_only_user,
    create_test_interactive_user,
)
from location.test_helpers import create_test_village
from social_protection.services import BeneficiaryService, GroupBeneficiaryService
from social_protection.tests.test_helpers import (
    add_group_to_benefit_plan,
    add_individual_to_benefit_plan,
    create_benefit_plan,
    create_group_with_individual,
    create_individual,
)

EXPORT_QUERY = """
    query ($bp: ID, $fields: [String], $columns: GenericScalar) {
      %s(benefitPlan_Id: $bp, isDeleted: false, fields: $fields, fieldsColumns: $columns)
    }
"""


class BeneficiaryExportColumnRightsTest(openIMISGraphQLTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = create_test_interactive_user(
            username="op3353SpAdmin", roles=[create_admin_role().id]
        )
        cls.admin_token = BaseTestContext(user=cls.admin).get_jwt()
        village = create_test_village({"name": "Op3353 Village", "code": "Op3353V"})
        district = village.parent.parent.code

        cls.beneficiary_only = create_right_only_user(
            "op3353BeneOnly", ["gql_beneficiary_search_perms"], district_codes=[district]
        )
        cls.beneficiary_only_token = BaseTestContext(user=cls.beneficiary_only).get_jwt()
        cls.beneficiary_and_group = create_right_only_user(
            "op3353BeneGroup",
            ["gql_beneficiary_search_perms", "gql_group_search_perms"],
            district_codes=[district],
        )
        cls.beneficiary_and_group_token = BaseTestContext(
            user=cls.beneficiary_and_group
        ).get_jwt()

        cls.group_plan = create_benefit_plan(
            cls.admin.username, payload_override={"code": "Op3353G", "type": "GROUP"}
        )
        _, cls.group, _ = create_group_with_individual(
            cls.admin.username,
            group_override={"code": "OP3353GROUPCODE", "location": village},
            individual_override={"location": village},
        )
        add_group_to_benefit_plan(
            GroupBeneficiaryService(cls.admin), cls.group, cls.group_plan
        )

        cls.individual_plan = create_benefit_plan(
            cls.admin.username, payload_override={"code": "Op3353I", "type": "INDIVIDUAL"}
        )
        cls.individual = create_individual(
            cls.admin.username,
            payload_override={"first_name": "Op3353Bene", "location": village},
        )
        add_individual_to_benefit_plan(
            BeneficiaryService(cls.admin), cls.individual, cls.individual_plan
        )

    def _export(self, field, plan, token, user, fields, columns=None):
        before = set(
            ExportableQueryModel.objects.filter(user=user).values_list("id", flat=True)
        )
        response = self.query(
            EXPORT_QUERY % field,
            variables={
                "bp": str(plan.id),
                "fields": fields,
                "columns": json.dumps(columns or {}),
            },
            headers={"HTTP_AUTHORIZATION": f"Bearer {token}"},
        )
        self.assertResponseNoErrors(response)
        export = ExportableQueryModel.objects.filter(user=user).exclude(id__in=before).get()
        export.content.open("rb")
        try:
            return export.content.read().decode()
        finally:
            export.content.close()

    def test_group_column_is_dropped_without_the_group_right(self):
        content = self._export(
            "groupBeneficiaryExport", self.group_plan,
            self.beneficiary_only_token, self.beneficiary_only,
            ["id", "group.id", "group.code", "json_ext"],
        )
        # The row itself is exported, with the group id the UI sends ...
        self.assertIn(str(self.group.id), content)
        # ... but not a column read from the group.
        self.assertNotIn("OP3353GROUPCODE", content)
        self.assertNotIn("group__code", content)

    def test_group_column_is_exported_with_the_group_right(self):
        content = self._export(
            "groupBeneficiaryExport", self.group_plan,
            self.beneficiary_and_group_token, self.beneficiary_and_group,
            ["id", "group.code", "json_ext"],
        )
        self.assertIn("OP3353GROUPCODE", content)

    def test_creator_password_hash_is_never_exported(self):
        password_hash = self.admin.i_user.password
        self.assertTrue(password_hash)
        content = self._export(
            "beneficiaryExport", self.individual_plan, self.admin_token, self.admin,
            ["id", "individual.first_name", "individual.userCreated.iUser.password", "json_ext"],
        )
        self.assertIn("Op3353Bene", content)
        self.assertNotIn(password_hash, content)
