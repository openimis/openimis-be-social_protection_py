from core.data_masking import DataMaskAbs
from social_protection.apps import SocialProtectionConfig


class BeneficiaryMask(DataMaskAbs):
    masking_model = 'Beneficiary'
    anon_fields = SocialProtectionConfig.beneficiary_mask_fields
    masking_enabled = SocialProtectionConfig.social_protection_masking_enabled


class GroupBeneficiaryMask(DataMaskAbs):
    masking_model = 'GroupBeneficiary'
    anon_fields = SocialProtectionConfig.group_beneficiary_mask_fields
    masking_enabled = SocialProtectionConfig.social_protection_masking_enabled
