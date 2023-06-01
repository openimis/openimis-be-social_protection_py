import logging

from core.services import BaseService
from core.signals import register_service_signal
from social_protection.models import (
    BenefitPlan,
    Beneficiary, Group, GroupIndividual
)
from social_protection.validation import (
    BeneficiaryValidation,
    BenefitPlanValidation, GroupValidation, GroupIndividualValidation
)
from abc import ABC
from typing import Type

from django.db import transaction

from core.models import HistoryModel
from core.services.utils import check_authentication as check_authentication, output_exception, \
    model_representation, output_result_success, build_delete_instance_payload
from core.validation.base import BaseModelValidation

logger = logging.getLogger(__name__)


class BenefitPlanService(BaseService):
    OBJECT_TYPE = BenefitPlan

    def __init__(self, user, validation_class=BenefitPlanValidation):
        super().__init__(user, validation_class)

    @register_service_signal('benefit_plan_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('benefit_plan_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('benefit_plan_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)


class BeneficiaryService(BaseService):
    OBJECT_TYPE = Beneficiary

    def __init__(self, user, validation_class=BeneficiaryValidation):
        super().__init__(user, validation_class)

    @register_service_signal('beneficiary_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('beneficiary_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('beneficiary_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)


class GroupService(BaseService):
    OBJECT_TYPE = Group

    def __init__(self, user, validation_class=GroupValidation):
        super().__init__(user, validation_class)

    @register_service_signal('group_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('group_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('group_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)


class GroupIndividualService(BaseService):
    OBJECT_TYPE = GroupIndividual

    def __init__(self, user, validation_class=GroupIndividualValidation):
        super().__init__(user, validation_class)

    @register_service_signal('group_individual_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('group_individual.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('group_individual.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)
