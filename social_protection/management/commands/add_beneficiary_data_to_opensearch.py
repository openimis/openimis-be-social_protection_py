from django.core.management.base import BaseCommand
from social_protection.models import Beneficiary
from social_protection.documents import BeneficiaryDocument


class Command(BaseCommand):
    help = 'Import beneficiary data into OpenSearch'

    def handle(self, *args, **options):
        # Initialize the index
        BeneficiaryDocument.init(index='beneficiary')
        # Loop through Beneficiary objects and index them
        for beneficiary in Beneficiary.objects.all():
            beneficiary_document = BeneficiaryDocument(
                meta={'id': beneficiary.id},  # Set the ID
                benefit_plan={
                    'code': beneficiary.benefit_plan.code,
                    'name': beneficiary.benefit_plan.name,
                },
                individual={
                    'first_name': beneficiary.individual.first_name,
                    'last_name': beneficiary.individual.last_name,
                    'dob': beneficiary.individual.dob,
                },
                id=beneficiary.id,
                status=beneficiary.status,
            )
            # Save the BeneficiaryDocument to index it in OpenSearch
            result = beneficiary_document.save()
            self.stdout.write(self.style.SUCCESS(result))
