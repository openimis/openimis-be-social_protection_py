from django.apps import AppConfig

from core.custom_filters import CustomFilterRegistryPoint


DEFAULT_CONFIG = {
    "gql_benefit_plan_search_perms": ["160001"],
    "gql_benefit_plan_create_perms": ["160002"],
    "gql_benefit_plan_update_perms": ["160003"],
    "gql_benefit_plan_delete_perms": ["160004"],
    "gql_beneficiary_search_perms": ["170001"],
    "gql_beneficiary_create_perms": ["170002"],
    "gql_beneficiary_update_perms": ["170003"],
    "gql_beneficiary_delete_perms": ["170004"],
}


class SocialProtectionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'social_protection'

    gql_benefit_plan_search_perms = None
    gql_benefit_plan_create_perms = None
    gql_benefit_plan_update_perms = None
    gql_benefit_plan_delete_perms = None
    gql_beneficiary_search_perms = None
    gql_beneficiary_create_perms = None
    gql_beneficiary_update_perms = None
    gql_beneficiary_delete_perms = None

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(self.name, DEFAULT_CONFIG)
        self.__load_config(cfg)

    @classmethod
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(SocialProtectionConfig, field):
                setattr(SocialProtectionConfig, field, cfg[field])

        # register custom filter
        from social_protection.custom_filters import BenefitPlanCustomFilterWizard
        CustomFilterRegistryPoint.register_custom_filters(
            module_name=cls.name,
            custom_filter_class_list=[BenefitPlanCustomFilterWizard]
        )
