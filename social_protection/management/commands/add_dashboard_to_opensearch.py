from django.conf import settings
from django.core.management.base import BaseCommand
from opensearchpy import OpenSearch
from pathlib import Path


class Command(BaseCommand):
    help = 'Import a dashboard into OpenSearch Dashboards.'

    def handle(self, *args, **kwargs):
        opensearch_url = 'http://0.0.0.0:9200'

        # Create an OpenSearch client with the correct Content-Type header
        opensearch = OpenSearch([opensearch_url], http_auth=('admin', 'admin'),
                                headers={"Content-Type": "application/json"})

        repo_name = f"openimis-be-social_protection_py"
        base_path = Path(settings.BASE_DIR)
        modules_directory = base_path.parent.parent
        module_directory = Path(modules_directory).joinpath(repo_name).joinpath('social_protection')
        import_file = module_directory.joinpath('import_data').joinpath('beneficiary_dashboard.ndjson')
        print(import_file)

        # Index the dashboard data
        with open(import_file, 'rb') as f:
            response = opensearch.bulk(
                index='dashboard_example',
                body=f
            )
            print(response)

        # Check if the import was successful
        if not response['errors']:
            self.stdout.write(self.style.SUCCESS('Dashboard imported successfully.'))
        else:
            self.stdout.write(self.style.ERROR('Failed to import dashboard.'))
            self.stdout.write(response)
