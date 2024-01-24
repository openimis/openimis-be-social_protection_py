import logging
import uuid

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.db import models
from django.db.models import Q, Value, Func, F
from django.db.models.functions import Concat
from pandas import DataFrame

from calculation.services import get_calculation_object
from core.services import BaseService
from core.signals import register_service_signal
from individual.models import IndividualDataSourceUpload, IndividualDataSource, Individual
from social_protection.apps import SocialProtectionConfig
from social_protection.models import (
    BenefitPlan,
    Beneficiary,
    BenefitPlanDataUploadRecords,
    GroupBeneficiary,
    JSONUpdate
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

    def _business_data_serializer(self, key, value):
        if key == 'id':
            beneficiary = Beneficiary.objects.get(id=value)
            individual = beneficiary.individual
            return f'{individual.first_name} {individual.last_name}'
        elif key == 'benefit_plan_id':
            benefit_plan = BenefitPlan.objects.get(id=value)
            return benefit_plan.__str__()
        elif key == 'individual_id':
            individual = Individual.objects.get(id=value)
            return f'{individual.first_name} {individual.last_name}'
        else:
            return value


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

    def validate_import_beneficiaries(self, upload_id: uuid, individual_sources, benefit_plan: BenefitPlan):
        dataframe = self._load_dataframe(individual_sources)
        validated_dataframe, invalid_items = self._validate_possible_beneficiaries(
            dataframe,
            benefit_plan,
            upload_id
        )
        return {'success': True, 'data': validated_dataframe, 'summary_invalid_items': invalid_items}

    def create_task_with_importing_valid_items(self, upload_id: uuid, benefit_plan: BenefitPlan):
        self._create_import_valid_items_task(benefit_plan, upload_id, self.user)

    def synchronize_data_for_reporting(self, upload_id: uuid, benefit_plan: BenefitPlan):
        self._synchronize_individual(upload_id)
        self._synchronize_beneficiary(benefit_plan, upload_id)

    def _validate_possible_beneficiaries(self, dataframe: DataFrame, benefit_plan: BenefitPlan, upload_id: uuid):
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
                if "uniqueness" in field_properties:
                    field_validation['validations'][f'{field}_uniqueness'] = self._handle_uniqueness(
                        row, field, field_properties, benefit_plan, dataframe
                    )
            validated_dataframe.append(field_validation)
            self.__save_validation_error_in_data_source(row, field_validation)
            return row

        dataframe.apply(validate_row, axis='columns')
        invalid_items = self.__fetch_summary_of_broken_items(upload_id)
        return validated_dataframe, invalid_items

    def _handle_uniqueness(self, row, field, field_properties, benefit_plan, dataframe):
        unique_class_validation = SocialProtectionConfig.unique_class_validation
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

    @register_service_signal('validation.create_task')
    def _create_import_valid_items_task(self, benefit_plan, upload_id, user):
        from social_protection.apps import SocialProtectionConfig
        from tasks_management.services import TaskService
        from tasks_management.apps import TasksManagementConfig
        from tasks_management.models import Task
        upload_record = BenefitPlanDataUploadRecords.objects.get(
            data_upload_id=upload_id,
            benefit_plan=benefit_plan,
            is_deleted=False
        )
        json_ext = {
            'benefit_plan_code': benefit_plan.code,
            'source_name': upload_record.data_upload.source_name,
            'workflow': upload_record.workflow,
            'percentage_of_invalid_items': self.__calculate_percentage_of_invalid_items(upload_id),
        }
        TaskService(user).create({
            'source': 'import_valid_items',
            'entity': upload_record,
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': SocialProtectionConfig.validation_import_valid_items,
            'json_ext': json_ext
        })

    def _synchronize_individual(self, upload_id):
        individuals_to_update = Individual.objects.filter(
            individualdatasource__upload=upload_id
        )
        individuals_to_update.update(json_ext=JSONUpdate(
            F('json_ext'),
            Value('{report_synch}'),
            Value('true'),
            output_field=models.JSONField()
        ))

    def _synchronize_beneficiary(self, benefit_plan, upload_id):
        synch_status = {'report_synch': 'true'}
        unique_uuids = list((
            Beneficiary.objects
                .filter(benefit_plan=benefit_plan, individual__individualdatasource__upload_id=upload_id)
                .values_list('id', flat=True)
                .distinct()
        ))
        beneficiaries = Beneficiary.objects.filter(
            id__in=unique_uuids
        )
        for beneficiary in beneficiaries:
            if beneficiary.json_ext:
                beneficiary.json_ext.update(synch_status)
            else:
                beneficiary.json_ext = synch_status
            beneficiary.save(username=self.user.username)

    def __fetch_summary_of_broken_items(self, upload_id):
        return list(IndividualDataSource.objects.filter(
            Q(is_deleted=False) &
            Q(upload_id=upload_id) &
            ~Q(validations__validation_errors=[])
        ).values_list('uuid', flat=True))

    def __fetch_summary_of_valid_items(self, upload_id):
        return list(IndividualDataSource.objects.filter(
            Q(is_deleted=False) &
            Q(upload_id=upload_id) &
            Q(validations__validation_errors=[])
        ).values_list('uuid', flat=True))

    def __calculate_percentage_of_invalid_items(self, upload_id):
        number_of_valid_items = len(self.__fetch_summary_of_valid_items(upload_id))
        number_of_invalid_items = len(self.__fetch_summary_of_broken_items(upload_id))
        total_items = number_of_invalid_items + number_of_valid_items

        if total_items == 0:
            percentage_of_invalid_items = 0
        else:
            percentage_of_invalid_items = (number_of_invalid_items / total_items) * 100

        percentage_of_invalid_items = round(percentage_of_invalid_items, 2)
        return percentage_of_invalid_items
