from django_opensearch_dsl import Document, fields as opensearch_fields
from django_opensearch_dsl.registries import registry
from social_protection.models import Beneficiary, BenefitPlan
from individual.models import Individual


@registry.register_document
class BeneficiaryDocument(Document):
    benefit_plan = opensearch_fields.ObjectField(properties={
        'code': opensearch_fields.KeywordField(),
        'name': opensearch_fields.KeywordField(),
    })
    individual = opensearch_fields.ObjectField(properties={
        'first_name': opensearch_fields.KeywordField(),
        'last_name': opensearch_fields.KeywordField(),
        'dob': opensearch_fields.DateField(),
    })
    status = opensearch_fields.KeywordField(fields={
        'status_key': opensearch_fields.KeywordField()}
    )

    class Index:
        name = 'beneficiary'  # Name of the Opensearch index
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
        auto_refresh = True

    class Django:
        model = Beneficiary
        related_models = [BenefitPlan, Individual]
        fields = [
            'id',
        ]
        queryset_pagination = 5000

    def get_instances_from_related(self, related_instance):
        """Define how to retrieve the Car instance(s) from the related model.
        The related_models option should be used with caution because it can lead to updating many items in the index.
        """
        if isinstance(related_instance, BenefitPlan):
            return related_instance.beneficiary_set.all()
        elif isinstance(related_instance, Individual):
            return related_instance.beneficiary_set.all()
