import json
import io
import logging
import uuid

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.db.models import Q
from pandas import DataFrame

from calculation.services import get_calculation_object
from core.services import BaseService
from core.signals import register_service_signal
from individual.models import IndividualDataSourceUpload, IndividualDataSource, Individual
from social_protection.apps import SocialProtectionConfig
from social_protection.models import (
    BenefitPlan,
    Beneficiary, GroupBeneficiary
)
from social_protection.validation import (
    BeneficiaryValidation,
    BenefitPlanValidation, GroupBeneficiaryValidation
)
from tasks_management.services import UpdateCheckerLogicServiceMixin, CheckerLogicServiceMixin
from workflow.systems.base import WorkflowHandler
from core.models import User

logger = logging.getLogger(__name__)


class BenefitPlanService(BaseService, UpdateCheckerLogicServiceMixin):
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


class BeneficiaryService(BaseService, CheckerLogicServiceMixin):
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

    def _data_for_json_ext_general(self, obj_data):
        beneficiary = Beneficiary.objects.get(id=obj_data.get("id"))
        individual = beneficiary.individual
        benefit_plan = beneficiary.benefit_plan
        individual_identity_string = f'{individual.first_name} {individual.last_name}'
        json_ext_data = {"individual_identity": individual_identity_string,
                         "benefit_plan_string": benefit_plan.__str__()}
        return json_ext_data

    def _data_for_json_ext_create(self, obj_data):
        individual = Individual.objects.get(id=obj_data.get("individual_id"))
        benefit_plan = BenefitPlan.objects.get(id=obj_data.get("individual_id"))
        individual_identity_string = f'{individual.first_name} {individual.last_name}'
        json_ext_data = {"individual_identity": individual_identity_string,
                         "benefit_plan_string": benefit_plan.__str__()}
        return json_ext_data

    def _data_for_json_ext_update(self, obj_data):
        return self._data_for_json_ext_general(obj_data)

    def _data_for_json_ext_delete(self, obj_data):
        return self._data_for_json_ext_general(obj_data)


class GroupBeneficiaryService(BaseService, CheckerLogicServiceMixin):
    OBJECT_TYPE = GroupBeneficiary

    def __init__(self, user, validation_class=GroupBeneficiaryValidation):
        super().__init__(user, validation_class)

    @register_service_signal('group_beneficiary_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('group_beneficiary_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('group_beneficiary_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)


class BeneficiaryImportService:
    import_loaders = {
        # .csv
        'text/csv': lambda f: pd.read_csv(f),
        # .xlsx
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': lambda f: pd.read_excel(f),
        # .xls
        'application/vnd.ms-excel': lambda f: pd.read_excel(f),
        # .ods
        'application/vnd.oasis.opendocument.spreadsheet': lambda f: pd.read_excel(f),
    }

    def __init__(self, user):
        super().__init__()
        self.user = user

    @transaction.atomic
    @register_service_signal('benefit_plan.import_beneficiaries')
    def import_beneficiaries(self,
                             import_file: InMemoryUploadedFile,
                             benefit_plan: BenefitPlan,
                             workflow: WorkflowHandler):
        upload = self._create_upload_entry(import_file.name)
        dataframe = self._load_import_file(import_file)
        self._validate_dataframe(dataframe)
        self._save_data_source(dataframe, upload)
        self._trigger_workflow(workflow, upload, benefit_plan)
        return {'success': True, 'data': {'upload_uuid': upload.uuid}}

    @register_service_signal('benefit_plan.validate_import_beneficiaries')
    def validate_import_beneficiaries(self, upload_id, individual_sources, benefit_plan: BenefitPlan):
        dataframe = self._load_dataframe(individual_sources)
        validated_dataframe = self._validate_possible_beneficiaries(dataframe, benefit_plan, upload_id)
        return {'success': True, 'data': validated_dataframe}

    @register_service_signal('benefit_plan.create_task_with_importing_valid_items')
    def create_task_with_importing_valid_items(self):
        pass

    def _validate_possible_beneficiaries(self, dataframe: DataFrame, benefit_plan: BenefitPlan, upload_id: uuid) -> DataFrame:
        schema_dict = benefit_plan.beneficiary_data_schema
        properties = schema_dict.get("properties", {})
        validated_dataframe = []

        def validate_row(row):
            field_validation = {'row': row.to_dict(), 'validations': {}}
            for field, field_properties in properties.items():
                if "validationCalculation" in field_properties:
                    field_validation['validations'][f'{field}'] = self._handle_validation_calculation(
                        row, field, field_properties
                    )
            validated_dataframe.append(field_validation)
            self.__save_validation_error_in_data_source(row, field_validation)
            return row

        dataframe.apply(validate_row, axis='columns')
        validated_dataframe['summary_invalid_items'] = self.__fetch_summary_of_broken_items(upload_id)
        return validated_dataframe

    def _handle_uniqueness(self, row, field, field_properties, benefit_plan, dataframe):
        unique_class_validation = 'DeduplicationValidationStrategy'
        calculation_uuid = SocialProtectionConfig.validation_calculation_uuid
        calculation = get_calculation_object(calculation_uuid)
        result_row = calculation.calculate_if_active_for_object(
            unique_class_validation,
            calculation_uuid,
            field,
            row[field],
            benefit_plan=benefit_plan.id,
            incoming_data=dataframe
        )
        return result_row

    def _handle_validation_calculation(self, row, field, field_properties):
        validation_calculation = field_properties.get("validationCalculation", {}).get("name")
        if not validation_calculation:
            raise ValueError("Missing validation name")
        calculation_uuid = SocialProtectionConfig.validation_calculation_uuid
        calculation = get_calculation_object(calculation_uuid)
        result_row = calculation.calculate_if_active_for_object(
            validation_calculation,
            calculation_uuid,
            field,
            row[field]
        )
        return result_row

    def _create_upload_entry(self, filename):
        upload = IndividualDataSourceUpload(source_name=filename, source_type='beneficiary import')
        upload.save(username=self.user.login_name)
        return upload

    def _validate_dataframe(self, dataframe: pd.DataFrame):
        if dataframe is None:
            raise ValueError("Unknown error while loading import file")
        if dataframe.empty:
            raise ValueError("Import file is empty")

    def _load_import_file(self, import_file) -> pd.DataFrame:
        if import_file.content_type not in self.import_loaders:
            raise ValueError("Unsupported content type: {}".format(import_file.content_type))

        return self.import_loaders[import_file.content_type](import_file)

    def _save_data_source(self, dataframe: pd.DataFrame, upload: IndividualDataSourceUpload):
        dataframe.apply(self._save_row, axis='columns', args=(upload,))

    def _save_row(self, row, upload):
        ds = IndividualDataSource(upload=upload, json_ext=row.to_dict(), validations={})
        ds.save(username=self.user.login_name)

    def _load_dataframe(self, individual_sources) -> pd.DataFrame:
        data_from_source = []
        for individual_source in individual_sources:
            json_ext = individual_source.json_ext
            individual_source.json_ext["id"] = individual_source.id
            data_from_source.append(json_ext)
        recreated_df = pd.DataFrame(data_from_source)
        return recreated_df

    def _trigger_workflow(self,
                          workflow: WorkflowHandler,
                          upload: IndividualDataSourceUpload,
                          benefit_plan: BenefitPlan):
        workflow.run({
            # Core user UUID required
            'user_uuid': str(User.objects.get(username=self.user.login_name).id),
            'benefit_plan_uuid': str(benefit_plan.uuid),
            'upload_uuid': str(upload.uuid),
        })
        upload.status = IndividualDataSourceUpload.Status.TRIGGERED
        upload.save(username=self.user.login_name)

    def __save_validation_error_in_data_source(self, row, field_validation):
        error_fields = []
        for key, value in field_validation['validations'].items():
            if not value['success']:
                error_fields.append({
                    "field_name": value['field_name'],
                    "note": value['note']
                })
        individual_data_source = IndividualDataSource.objects.get(id=row['id'])
        validation_column = {'validation_errors': error_fields}
        individual_data_source.validations = validation_column
        individual_data_source.save(username=self.user.username)

    def __fetch_summary_of_broken_items(self, upload_id):
        return list(IndividualDataSource.objects.filter(
            Q(is_deleted=False) &
            Q(upload_id=upload_id) &
            ~Q(validations__validation_errors=[])
        ).values_list('uuid', flat=True))
