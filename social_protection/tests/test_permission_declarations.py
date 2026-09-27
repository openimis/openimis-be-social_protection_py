"""
Guard rails on social_protection's rights declaration.

Same structure as `claim`, `insuree` and `individual`: `DJANGO_PERMS` by entity then by
action, `_PERM_CFG` deriving the config keys from it, and one `get_rights` per model
which is only an access point.

What is locked down here:
  * the 20 identifiers as deployed and as `permissions_map.json` carries them -
    changing one withdraws access from every role that holds it;
  * a config key with no class attribute is never loaded by `__load_config` and
    reading it raises AttributeError - the right becomes unenforceable;
  * `has_perms([])` returns True, so an empty list grants to everybody;
  * the `GroupBeneficiary` -> `beneficiary` entity alias, which is a decision and not
    an oversight: there is no identifier specific to group beneficiaries;
  * the project's `enroll` / `timeEntry` business actions, which have to stay distinct
    from `create` / `update`.
"""

import json
import os

from django.test import TestCase

from social_protection.apps import (
    DJANGO_PERMS,
    SocialProtectionConfig,
    _PERM_CFG,
    configured_perms,
    django_perms,
    perms,
)
from social_protection.models import (
    Activity,
    Beneficiary,
    BeneficiaryProjectEnrollment,
    BeneficiaryProjectTimeEntry,
    BenefitPlan,
    GroupBeneficiary,
    GroupBeneficiaryProjectEnrollment,
    GroupBeneficiaryProjectTimeEntry,
    Project,
)

# The identifiers as deployed. Changing one is incompatible with the existing roles:
# this test has to be updated *and* the new right granted.
EXPECTED_RIGHTS = {
    "gql_benefit_plan_search_perms": ["160001"],
    "gql_benefit_plan_create_perms": ["160002"],
    "gql_benefit_plan_update_perms": ["160003"],
    "gql_benefit_plan_delete_perms": ["160004"],
    "gql_benefit_plan_close_perms": ["160005"],
    "gql_beneficiary_search_perms": ["170001"],
    "gql_beneficiary_create_perms": ["170002"],
    "gql_beneficiary_update_perms": ["170003"],
    "gql_beneficiary_delete_perms": ["170004"],
    "gql_schema_search_perms": ["171001"],
    "gql_schema_create_perms": ["171002"],
    "gql_schema_update_perms": ["171003"],
    "gql_schema_delete_perms": ["171004"],
    "gql_activity_search_perms": ["208001"],
    "gql_project_search_perms": ["209001"],
    "gql_project_create_perms": ["209002"],
    "gql_project_update_perms": ["209003"],
    "gql_project_delete_perms": ["209004"],
    "gql_project_beneficiary_enroll_perms": ["209005"],
    "gql_project_beneficiary_time_entry_perms": ["209006"],
}

# The `permissions_map.json` keys that carry these same identifiers. The names there
# are the openIMIS catalogue's (`social_protection.benefit_plan_search`), distinct from
# the django names declared in DJANGO_PERMS: only the integer is authoritative.
EXPECTED_MAP_ENTRIES = {
    "social_protection.benefit_plan_search": "160001",
    "social_protection.benefit_plan_create": "160002",
    "social_protection.benefit_plan_update": "160003",
    "social_protection.benefit_plan_delete": "160004",
    "social_protection.benefit_plan_close": "160005",
    "social_protection.beneficiary_search": "170001",
    "social_protection.beneficiary_create": "170002",
    "social_protection.beneficiary_update": "170003",
    "social_protection.beneficiary_delete": "170004",
    "social_protection.schema_search": "171001",
    "social_protection.schema_create": "171002",
    "social_protection.schema_update": "171003",
    "social_protection.schema_delete": "171004",
    "social_protection.activity_search": "208001",
    "social_protection.project_search": "209001",
    "social_protection.project_create": "209002",
    "social_protection.project_update": "209003",
    "social_protection.project_delete": "209004",
    "social_protection.project_beneficiary_enroll": "209005",
    "social_protection.project_beneficiary_time_entry": "209006",
}


def _load_permissions_map():
    """`permissions_map.json` lives in the assembly, not in the package."""
    from django.conf import settings

    candidates = [
        os.path.join(str(settings.BASE_DIR), "permissions_map.json"),
        os.path.join(os.path.dirname(str(settings.BASE_DIR)), "permissions_map.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as handle:
                return json.load(handle)
    return None


class SocialProtectionPermissionDeclarationTestCase(TestCase):
    def test_right_ids_unchanged(self):
        self.assertEqual(
            {key: getattr(SocialProtectionConfig, key) for key in EXPECTED_RIGHTS},
            EXPECTED_RIGHTS,
        )

    def test_perm_cfg_covers_every_declared_action(self):
        declared = {
            (entity, action)
            for entity, actions in DJANGO_PERMS.items()
            for action in actions
        }
        self.assertEqual(set(_PERM_CFG.values()), declared)

    def test_perm_cfg_matches_config_attributes(self):
        """`__load_config` ignores the keys with no class attribute."""
        missing = [key for key in _PERM_CFG if not hasattr(SocialProtectionConfig, key)]
        self.assertEqual(missing, [])

    def test_no_right_list_is_empty(self):
        empty = [key for key in _PERM_CFG if not getattr(SocialProtectionConfig, key)]
        self.assertEqual(empty, [])

    def test_attributes_carry_the_declared_right(self):
        """
        The rights are constants set from DJANGO_PERMS: the attribute must equal the
        declaration, without going through the config.
        """
        for key, (entity, action) in _PERM_CFG.items():
            with self.subTest(key=key):
                self.assertEqual(
                    getattr(SocialProtectionConfig, key), perms(entity, action)
                )

    def test_rights_are_not_in_the_default_config(self):
        """
        Rights are no longer configurable: `DEFAULT_CONFIG` must carry no `_perms` key,
        otherwise `ready()` would reload them from the database.
        """
        from social_protection.apps import DEFAULT_CONFIG

        self.assertEqual([k for k in DEFAULT_CONFIG if k.endswith("_perms")], [])

    def test_no_shared_right_ids(self):
        """No identifier sharing is intended in this module."""
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                seen.setdefault(right_id, []).append((entity, action))
        shared = {rid: who for rid, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_are_unique(self):
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                seen.setdefault(name, []).append(f"{entity}.{action}")
        shared = {name: who for name, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_use_the_app_label(self):
        """The app_label in this assembly is `social_protection`."""
        self.assertEqual(BenefitPlan._meta.app_label, "social_protection")
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                with self.subTest(entity=entity, action=action):
                    self.assertTrue(name.startswith("social_protection."))

    def test_project_business_actions_are_distinct_rights(self):
        """
        Enrolling a beneficiary and recording its progress are neither the creation nor
        the modification of a project: three distinct rights, grantable separately.
        """
        self.assertNotEqual(perms("project", "enroll"), perms("project", "create"))
        self.assertNotEqual(perms("project", "timeEntry"), perms("project", "update"))
        self.assertNotEqual(perms("project", "enroll"), perms("project", "timeEntry"))

    def test_close_is_not_delete(self):
        self.assertNotEqual(
            perms("benefitPlan", "close"), perms("benefitPlan", "delete")
        )

    def test_unknown_entity_or_action_raises(self):
        with self.assertRaises(KeyError):
            perms("nosuchentity", "query")
        with self.assertRaises(KeyError):
            perms("benefitPlan", "nosuchaction")
        with self.assertRaises(KeyError):
            django_perms("benefitPlan", "nosuchaction")

    # --- the access points through the models -----------------------------
    def test_model_exposes_every_action_of_its_entity(self):
        for model, entity in (
            (BenefitPlan, "benefitPlan"),
            (Beneficiary, "beneficiary"),
            (Activity, "activity"),
            (Project, "project"),
        ):
            for action in DJANGO_PERMS[entity]:
                with self.subTest(model=model.__name__, action=action):
                    self.assertEqual(
                        model.get_rights(action), configured_perms(entity, action)
                    )
                    self.assertTrue(model.get_rights(action))

    def test_group_beneficiary_aliases_the_beneficiary_entity(self):
        """
        A decision, not an oversight: there is neither an identifier nor a config key
        specific to group beneficiaries, and the group mutations read
        `gql_beneficiary_*`.
        """
        for action in DJANGO_PERMS["beneficiary"]:
            with self.subTest(action=action):
                self.assertEqual(
                    GroupBeneficiary.get_rights(action),
                    Beneficiary.get_rights(action),
                )

    def test_enrollment_models_take_the_project_enroll_right(self):
        for model in (BeneficiaryProjectEnrollment, GroupBeneficiaryProjectEnrollment):
            with self.subTest(model=model.__name__):
                self.assertEqual(
                    model.get_rights("create"), configured_perms("project", "enroll")
                )
                self.assertEqual(
                    model.get_rights("delete"), configured_perms("project", "enroll")
                )
                # And above all not the right to create a project.
                self.assertNotEqual(model.get_rights("create"), perms("project", "create"))

    def test_time_entry_models_take_the_project_time_entry_right(self):
        for model in (
            BeneficiaryProjectTimeEntry,
            GroupBeneficiaryProjectTimeEntry,
        ):
            with self.subTest(model=model.__name__):
                self.assertEqual(
                    model.get_rights("create"),
                    configured_perms("project", "timeEntry"),
                )
                self.assertEqual(
                    model.get_rights("update"),
                    configured_perms("project", "timeEntry"),
                )

    def test_model_returns_none_for_an_undeclared_action(self):
        """None means "no rule": the caller must fail closed."""
        self.assertIsNone(BenefitPlan.get_rights("nosuchaction"))
        self.assertIsNone(Activity.get_rights("create"))
        self.assertIsNone(BeneficiaryProjectEnrollment.get_rights("query"))

    def test_model_reads_the_configured_value_not_the_declared_default(self):
        """
        ModuleConfiguration may override a right; the check must read the configured
        value, where `perms()` returns the declared default.
        """
        original = SocialProtectionConfig.gql_benefit_plan_search_perms
        try:
            SocialProtectionConfig.gql_benefit_plan_search_perms = ["999999"]
            self.assertEqual(BenefitPlan.get_rights("query"), ["999999"])
            self.assertEqual(perms("benefitPlan", "query"), ["160001"])
        finally:
            SocialProtectionConfig.gql_benefit_plan_search_perms = original

    def test_ids_match_permissions_map(self):
        """The assembly's rights map must carry the same integers."""
        mapping = _load_permissions_map()
        if mapping is None:
            self.skipTest("permissions_map.json not found in this assembly")
        for key, right_id in EXPECTED_MAP_ENTRIES.items():
            with self.subTest(key=key):
                self.assertEqual(str(mapping.get(key)), right_id)
        declared_ids = {
            str(right_id)
            for actions in DJANGO_PERMS.values()
            for _, right_id in actions.values()
        }
        self.assertEqual(set(EXPECTED_MAP_ENTRIES.values()), declared_ids)
