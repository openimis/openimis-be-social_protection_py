from django.test import TestCase
from social_protection.models import BenefitPlan, IndividualDataSource, IndividualDataSourceUpload
from social_protection.services import BeneficiaryImportService
from social_protection.tests.helpers import LogInHelper
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
        cls.benefit_plan = BenefitPlan.objects.create(code="BP1", name="Benefit Plan 1")
        cls.upload = cls.__create_individual_data_source_upload()
        cls.individual_sources = cls.__create_individual_sources(cls.upload)

    def test_validate_import_beneficiaries(self):
        result = self.service.validate_import_beneficiaries(
            self.upload.id,
            self.individual_sources,
            self.benefit_plan
        )
        self.assertTrue(result.get('success', False))

    def test_calculate_percentage_of_invalid_items(self):
        result = self.service.__calculate_percentage_of_invalid_items(self.upload.id)
        self.assertEqual(result, 0.0)

    def test_load_dataframe(self):
        result = self.service._load_dataframe(self.individual_sources)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.size, len(self.individual_sources))

    @classmethod
    def __create_individual_data_source_upload(cls):
        object_data = {
            'source_name': 'Sample Source',
            'source_type': 'Sample Type',
            'status': IndividualDataSourceUpload.Status.PENDING,
            'error': {}
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
            'validations': {}
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
    def __create_individual_sources(cls, upload):
        cls.__create_individual_data_source(upload),
        cls.__create_individual_data_source(upload),
        cls.__create_individual_data_source(upload)
        return IndividualDataSource.objects.filter(upload_id=upload.id)
