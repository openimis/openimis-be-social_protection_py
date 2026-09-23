import logging
import json

from django.apps import AppConfig

from core.custom_filters import CustomFilterRegistryPoint
from core.data_masking import MaskingClassRegistryPoint
from core.module_config_registry import register_reloader
from core.rights_declaration import RightsDeclaration

logger = logging.getLogger(__name__)

MODULE_NAME = "social_protection"

# Rights, by entity then by action. Five entities, five distinct blocks of identifiers
# in the openIMIS catalogue: `benefitPlan` (160xxx), `beneficiary` (170xxx), `schema`
# (171xxx), `activity` (208xxx) and `project` (209xxx). No identifier is shared.
#
# The django names all carry the `social_protection` app_label: no model of the module
# declares a `Meta.app_label`, so the app_label is the app's name.
#
# `groupBeneficiary` deliberately does not appear here: the
# Create/Update/DeleteGroupBeneficiary mutations check the same `gql_beneficiary_*`
# keys as individual beneficiaries, and there is neither an identifier nor a config key
# specific to group beneficiaries. `GroupBeneficiary.get_rights` says so on the model
# rather than inventing an entity here with no right of its own.
DJANGO_PERMS = {
    "benefitPlan": {
        "query": ("social_protection.view_benefitplan", 160001),
        "create": ("social_protection.add_benefitplan", 160002),
        "update": ("social_protection.change_benefitplan", 160003),
        "delete": ("social_protection.delete_benefitplan", 160004),
        # A business action: closing a programme is neither a deletion (the
        # programme stays readable and historised) nor an ordinary modification, and
        # the catalogue already gives it 160005.
        "close": ("social_protection.close_benefitplan", 160005),
    },
    "beneficiary": {
        "query": ("social_protection.view_beneficiary", 170001),
        "create": ("social_protection.add_beneficiary", 170002),
        "update": ("social_protection.change_beneficiary", 170003),
        "delete": ("social_protection.delete_beneficiary", 170004),
    },
    # `schema` is not a model: it is the field-level right over
    # `BenefitPlan.beneficiary_data_schema` and over the beneficiaries' `json_ext`
    # (see `check_perms_for_field` in gql_mutations and `JsonExtMixin` in gql_queries).
    # The django names stay declarative: nothing grants them as long as no
    # `Meta.permissions` carries them.
    "schema": {
        "query": ("social_protection.view_beneficiary_data_schema", 171001),
        "create": ("social_protection.add_beneficiary_data_schema", 171002),
        "update": ("social_protection.change_beneficiary_data_schema", 171003),
        # A dormant declaration: 171004 exists in the catalogue and in the config,
        # but no call site reads it. Kept so as not to withdraw a right that roles may
        # already hold.
        "delete": ("social_protection.delete_beneficiary_data_schema", 171004),
    },
    "activity": {
        "query": ("social_protection.view_activity", 208001),
    },
    "project": {
        "query": ("social_protection.view_project", 209001),
        "create": ("social_protection.add_project", 209002),
        "update": ("social_protection.change_project", 209003),
        "delete": ("social_protection.delete_project", 209004),
        # The project's business actions, non-canonical: enrolling a beneficiary
        # (individual or group) in a project, and recording its daily progress. These
        # are neither a `create` nor an `update` of a project - they are grantable and
        # revocable separately, and the catalogue gives them identifiers of their own.
        # They are carried by `project` and not by the enrolment models because a
        # single right covers both variants (individual and group beneficiary).
        "enroll": ("social_protection.enroll_project_beneficiary", 209005),
        "timeEntry": ("social_protection.record_project_time_entry", 209006),
    },
}

_PERM_CFG = {
    "gql_benefit_plan_search_perms": ("benefitPlan", "query"),
    "gql_benefit_plan_create_perms": ("benefitPlan", "create"),
    "gql_benefit_plan_update_perms": ("benefitPlan", "update"),
    "gql_benefit_plan_delete_perms": ("benefitPlan", "delete"),
    "gql_benefit_plan_close_perms": ("benefitPlan", "close"),
    "gql_beneficiary_search_perms": ("beneficiary", "query"),
    "gql_beneficiary_create_perms": ("beneficiary", "create"),
    "gql_beneficiary_update_perms": ("beneficiary", "update"),
    "gql_beneficiary_delete_perms": ("beneficiary", "delete"),
    "gql_schema_search_perms": ("schema", "query"),
    "gql_schema_create_perms": ("schema", "create"),
    "gql_schema_update_perms": ("schema", "update"),
    "gql_schema_delete_perms": ("schema", "delete"),
    "gql_activity_search_perms": ("activity", "query"),
    "gql_project_search_perms": ("project", "query"),
    "gql_project_create_perms": ("project", "create"),
    "gql_project_update_perms": ("project", "update"),
    "gql_project_delete_perms": ("project", "delete"),
    "gql_project_beneficiary_enroll_perms": ("project", "enroll"),
    "gql_project_beneficiary_time_entry_perms": ("project", "timeEntry"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require

DEFAULT_CONFIG = {


    # Create task for model instead of performing crud action
    "gql_check_benefit_plan_update": True,
    "gql_check_beneficiary_crud": True,
    "gql_check_group_beneficiary_crud": True,
    "unique_class_validation": "DeduplicationValidationStrategy",
    "validation_calculation_uuid": "4362f958-5894-435b-9bda-df6cadf88352",
    "enable_maker_checker_for_beneficiary_upload": True,
    "enable_maker_checker_for_beneficiary_update": True,
    "validation_import_valid_items": "validation.import_valid_items",
    "validation_import_valid_items": "validation.import_valid_items",
    "validation_import_group_valid_items": "validation.import_group_valid_items",
    "validation_upload_valid_items": "validation.upload_valid_items",
    "validation_download_invalid_items": "validation.download_invalid_items",
    "benefit_plan_suspend": "benefit_plan.benefit_plan_suspend",

    "validation_import_valid_items_workflow": "beneficiary-import-valid-items.beneficiary-import-valid-items",
    "validation_upload_valid_items_workflow": "beneficiary-upload-valid-items.beneficiary-upload-valid-items",
    "validation_enrollment": "validation-enrollment",
    "validation_group_enrollment": "validation-group-enrollment",

    "enable_maker_checker_logic_enrollment": True,
    "enable_maker_checker_for_group_upload": True,
    "beneficiary_mask_fields": [
        'json_ext.beneficiary_data_source',
        'json_ext.educated_level'
    ],
    "group_beneficiary_mask_fields": [
        'json_ext.beneficiary_data_source',
        'json_ext.educated_level'
    ],
    "beneficiary_base_fields": [
        'first_name', 'last_name', 'dob', 'location_name', 'location_code', 'id'
    ],
    "social_protection_masking_enabled": True,
    "enable_python_workflows": True,
    "default_beneficiary_status": "POTENTIAL",
}


class SocialProtectionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = MODULE_NAME
    verbose_name = 'Social Protection'

    # Rights: constants, no longer overridable. They go neither through DEFAULT_CFG
    # nor through ready(): `ModuleConfiguration.get_or_default` now ignores any
    # `_perms` key stored in the database.
    gql_benefit_plan_search_perms = RIGHTS.perms("benefitPlan", "query")
    gql_benefit_plan_create_perms = RIGHTS.perms("benefitPlan", "create")
    gql_benefit_plan_update_perms = RIGHTS.perms("benefitPlan", "update")
    gql_benefit_plan_delete_perms = RIGHTS.perms("benefitPlan", "delete")
    gql_benefit_plan_close_perms = RIGHTS.perms("benefitPlan", "close")
    gql_beneficiary_search_perms = RIGHTS.perms("beneficiary", "query")
    gql_beneficiary_create_perms = RIGHTS.perms("beneficiary", "create")
    gql_beneficiary_update_perms = RIGHTS.perms("beneficiary", "update")
    gql_beneficiary_delete_perms = RIGHTS.perms("beneficiary", "delete")
    gql_schema_search_perms = RIGHTS.perms("schema", "query")
    gql_schema_create_perms = RIGHTS.perms("schema", "create")
    gql_schema_update_perms = RIGHTS.perms("schema", "update")
    gql_schema_delete_perms = RIGHTS.perms("schema", "delete")
    gql_activity_search_perms = RIGHTS.perms("activity", "query")
    gql_project_search_perms = RIGHTS.perms("project", "query")
    gql_project_create_perms = RIGHTS.perms("project", "create")
    gql_project_update_perms = RIGHTS.perms("project", "update")
    gql_project_delete_perms = RIGHTS.perms("project", "delete")
    gql_project_beneficiary_enroll_perms = RIGHTS.perms("project", "enroll")
    gql_project_beneficiary_time_entry_perms = RIGHTS.perms(
        "project", "timeEntry"
    )

    gql_check_benefit_plan_update = None
    gql_check_beneficiary_crud = None
    gql_check_group_beneficiary_crud = None
    unique_class_validation = None
    validation_calculation_uuid = None
    validation_import_valid_items = None
    validation_upload_valid_items = None
    validation_download_invalid_items = None
    validation_import_valid_items_workflow = None
    validation_upload_valid_items_workflow = None
    validation_enrollment = None
    validation_group_enrollment = None
    validation_import_group_valid_items = None
    benefit_plan_suspend = None

    enable_maker_checker_for_beneficiary_upload = None
    enable_maker_checker_for_beneficiary_update = None

    enable_python_workflows = None
    enable_maker_checker_logic_enrollment = None
    enable_maker_checker_for_group_upload = None
    beneficiary_mask_fields = None
    group_beneficiary_mask_fields = None
    beneficiary_base_fields = None
    social_protection_masking_enabled = None

    default_beneficiary_status = None

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(self.name, DEFAULT_CONFIG)
        self.__load_config(cfg)
        self._set_up_workflows()
        self.__register_masking_class()
        register_reloader(self.name, self._reload_module_config)

    def _reload_module_config(self, instance):
        # `instance._cfg` and not `json.loads(instance.config)`: the property is what
        # strips the rights, which are no longer configurable.
        config = {**DEFAULT_CONFIG, **instance._cfg}
        self.__load_config(config)

        # Workflow needs to be re-registered, otherwise default/invalid ones would apply
        self._set_up_workflows()

        # TODO: handle reloading of masking configs
        logger.info(f"Reloaded app configs (except masking configs) for {self.name} module")

    def _set_up_workflows(self):
        from workflow.systems.python import PythonWorkflowAdaptor
        from social_protection.workflows import process_import_beneficiaries_workflow, \
            process_update_beneficiaries_workflow, \
            process_import_valid_beneficiaries_workflow, \
            process_update_valid_beneficiaries_workflow

        if self.enable_python_workflows:
            PythonWorkflowAdaptor.register_workflow(
                'Python Beneficiaries Upload',
                'socialProtection',
                process_import_beneficiaries_workflow
            )
            PythonWorkflowAdaptor.register_workflow(
                'Python Beneficiaries Update',
                'socialProtection',
                process_update_beneficiaries_workflow
            )
            PythonWorkflowAdaptor.register_workflow(
                'Python Beneficiaries Valid Upload',
                'socialProtection',
                process_import_valid_beneficiaries_workflow
            )
            PythonWorkflowAdaptor.register_workflow(
                'Python Beneficiaries Valid Update',
                'socialProtection',
                process_update_valid_beneficiaries_workflow
            )

        # Replace default setup for invalid workflow to be python one
        if SocialProtectionConfig.enable_python_workflows is True:

            # Resolve Maker-Checker Workflows Overwrite
            if self.validation_import_valid_items_workflow == DEFAULT_CONFIG['validation_import_valid_items_workflow']:
                SocialProtectionConfig.validation_import_valid_items_workflow \
                    = 'socialProtection.Python Beneficiaries Valid Upload'

            if self.validation_upload_valid_items_workflow == DEFAULT_CONFIG['validation_upload_valid_items_workflow']:
                SocialProtectionConfig.validation_upload_valid_items_workflow \
                    = 'socialProtection.Python Beneficiaries Valid Update'

            # # Create Maker-Checker Logic tasks
            # if self.validation_import_valid_items == DEFAULT_CONFIG['validation_import_valid_items']:
            #     SocialProtectionConfig.validation_import_valid_items \
            #         = 'socialProtection.Python Beneficiaries Valid Upload'
            # if self.validation_upload_valid_items == DEFAULT_CONFIG['validation_upload_valid_items']:
            #     SocialProtectionConfig.validation_upload_valid_items \
            #         = 'socialProtection.Python Beneficiaries Valid Update'

    @classmethod
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(SocialProtectionConfig, field):
                setattr(SocialProtectionConfig, field, cfg[field])

        from social_protection.custom_filters import BenefitPlanCustomFilterWizard
        CustomFilterRegistryPoint.register_custom_filters(
            module_name=cls.name,
            custom_filter_class_list=[BenefitPlanCustomFilterWizard]
        )

    def __register_masking_class(cls):
        from social_protection.data_masking import (
            BeneficiaryMask,
            GroupBeneficiaryMask
        )
        MaskingClassRegistryPoint.register_masking_class(
            masking_class_list=[BeneficiaryMask(), GroupBeneficiaryMask()]
        )

    @staticmethod
    def get_beneficiary_upload_file_path(benefit_plan_id, file_name=None):
        if file_name:
            return f"beneficiary_upload/benefit_plan_{benefit_plan_id}/{file_name}"
        return f"beneficiary_upload/benefit_plan_{benefit_plan_id}"
