from django.apps import apps

from social_protection.apps import SocialProtectionConfig

# Check if the 'opensearch_reports' app is in INSTALLED_APPS
if 'opensearch_reports' in apps.app_configs and SocialProtectionConfig.opensearch_synch:
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
        date_created = opensearch_fields.DateField()
        json_ext = opensearch_fields.ObjectField()

        class Index:
            name = 'beneficiary'
            settings = {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
            auto_refresh = True

        class Django:
            model = Beneficiary
            related_models = [BenefitPlan, Individual]
            fields = [
                'id'
            ]
            queryset_pagination = 5000

        def get_instances_from_related(self, related_instance):
            if isinstance(related_instance, BenefitPlan):
                return related_instance.beneficiary_set.all()
            elif isinstance(related_instance, Individual):
                return related_instance.beneficiary_set.all()

        def prepare_json_ext(self, instance):
            json_ext_data = instance.json_ext
            json_data = self.__flatten_dict(json_ext_data)
            return json_data

        def __flatten_dict(self, d, parent_key='', sep='__'):
            items = {}
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.update(self.__flatten_dict(v, new_key, sep=sep))
                else:
                    items[new_key] = v
            return items

