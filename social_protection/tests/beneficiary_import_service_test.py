from django.test import TestCase
from social_protection.models import BenefitPlan, BenefitPlanDataUploadRecords
from individual.models import IndividualDataSource, IndividualDataSourceUpload
from social_protection.services import BeneficiaryImportService
from core.test_helpers import LogInHelper
from social_protection.tests.data import service_add_payload
from individual.models import Individual
from individual.tests.data import service_add_individual_payload
import pandas as pd


class BeneficiaryImportServiceTest(TestCase):
    user = None
    service = None
    benefit_plan = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = BeneficiaryImportService(cls.user)
        cls.benefit_plan = cls.__create_benefit_plan()
        cls.upload = cls.__create_individual_data_source_upload()
        cls.individual_sources = cls.__create_individual_sources(cls.upload)
        cls.upload_record = cls.__create_benefit_plan_data_upload_records(
            cls.upload,
            cls.benefit_plan,
            'test-workflow',
        )

    def test_validate_import_beneficiaries(self):
        result = self.service.validate_import_beneficiaries(
            self.upload.id,
            self.individual_sources,
            self.benefit_plan
        )
        self.assertTrue(result.get('success', True))

    def test_validate_possible_beneficiares(self):
        dataframe = self.service._load_dataframe(self.individual_sources)
        validated_dataframe, invalid_items = self.service._validate_possible_beneficiaries(
            dataframe,
            self.benefit_plan,
            self.upload.id
        )
        self.assertIsInstance(validated_dataframe, list)
        self.assertIsInstance(invalid_items, list)

    def test_load_dataframe(self):
        result = self.service._load_dataframe(self.individual_sources)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.size, len(self.individual_sources))

    def test_create_task_with_importing_valid_items(self):
        self.service.create_task_with_importing_valid_items(self.upload.id, self.benefit_plan)

    @classmethod
    def __create_individual_data_source_upload(cls):
        object_data = {
            'source_name': 'Sample Source',
            'source_type': 'Sample Type',
            'status': IndividualDataSourceUpload.Status.PENDING,
            'error': {},
            'json_ext': {}
        }

        individual_data_source_upload = IndividualDataSourceUpload(**object_data)
        individual_data_source_upload.save(username=cls.user.username)

        return individual_data_source_upload

    @classmethod
    def __create_individual_data_source(cls, individual_data_source_upload_instance):
        individual_instance = cls.__create_individual()

        object_data = {
            'individual': individual_instance,
            'upload': individual_data_source_upload_instance,
            'validations': {},
            'json_ext': {}
        }

        individual_data_source = IndividualDataSource(**object_data)
        individual_data_source.save(username=cls.user.username)

        return individual_data_source

    @classmethod
    def __create_individual(cls):
        object_data = {
            **service_add_individual_payload
        }

        individual = Individual(**object_data)
        individual.save(username=cls.user.username)

        return individual

    @classmethod
    def __create_benefit_plan(cls):
        object_data = {
            **service_add_payload
        }

        benefit_plan = BenefitPlan(**object_data)
        benefit_plan.save(username=cls.user.username)

        return benefit_plan

    @classmethod
    def __create_individual_sources(cls, upload):
        cls.__create_individual_data_source(upload),
        cls.__create_individual_data_source(upload),
        cls.__create_individual_data_source(upload)
        return IndividualDataSource.objects.filter(upload_id=upload.id)

    @classmethod
    def __create_benefit_plan_data_upload_records(cls, data_upload, benefit_plan, workflow):
        record_upload = BenefitPlanDataUploadRecords(
            data_upload=data_upload,
            benefit_plan=benefit_plan,
            workflow=workflow
        )
        record_upload.save(username=cls.user.username)
        return record_upload
