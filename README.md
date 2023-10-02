# openIMIS Backend social_protection reference module
This repository holds the files of the openIMIS Backend social_protection reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

## ORM mapping:
* social_protection_benefitplan, social_protection_historicalbenefitplan > BenefitPlan
* social_protection_beneficiary, social_protection_historicalbeneficiary > Beneficiary
* social_protection_benefitplandatauploadsrecords, social_protection_historicalbenefitplandatauploadsrecords > BenefitPlanDataUploadRecords
* social_protection_groupbeneficiary, social_protection_historicalgroupbeneficiary > GroupBeneficiary

## GraphQl Queries
* benefitPlan
* beneficiary
* groupBeneficiary
* beneficiaryDataUploadHistory
* bfCodeValidity
* bfNameValidity
* bfNameValidity
* bfSchemaValidity
* beneficiaryExport
* groupBeneficiaryExport

## GraphQL Mutations - each mutation emits default signals and return standard error lists (cfr. openimis-be-core_py)
* createBenefitPlan
* updateBenefitPlan
* deleteBenefitPlan
* createBeneficiary
* updateBeneficiary
* deleteBeneficiary
* createGroupBeneficiary
* updateGroupBeneficiary
* deleteGroupBeeficiary

## Services
- BenefitPlan
  - create
  - update
  - delete
  - create_update_task
- Beneficiary
  - create
  - update
  - delete
- GroupBeneficiary
  - create
  - update
  - delete
- BeneficiaryImport
  - import_beneficiaries

## Configuration options (can be changed via core.ModuleConfiguration)
* gql_benefit_plan_search_perms: required rights to call benefitPlan GraphQL Query (default: ["160001"])
* gql_benefit_plan_create_perms: required rights to call createBenefitPlan GraphQL Mutation (default: ["160002"])
* gql_benefit_plan_update_perms: required rights to call updateBenefitPlan GraphQL Mutation (default: ["160003"])
* gql_benefit_plan_delete_perms: required rights to call deleteBenefitPlan GraphQL Mutation (default: ["160004"])
* gql_beneficiary_search_perms: required rights to call beneficiary and groupBeneficiary GraphQL Mutation (default: ["170001"])
* gql_beneficiary_create_perms: required rights to call createBeneficiary and createGroupBeneficiary GraphQL Mutation (default: ["160002"])
* gql_beneficiary_update_perms: required rights to call updateBeneficiary and updateGroupBeneficiary GraphQL Mutation (default: ["160003"])
* gql_beneficiary_delete_perms: required rights to call deleteBeneficiary and deleteGroupBeneficiary GraphQL Mutation (default: ["170004"])

* gql_check_benefit_plan_update: specifies whether Benefit Plan update should be updated using task based approval (default: True)
* gql_check_beneficiary_crud: specifies whether Beneficiary CRUD should be use task based approval (default: True)
* gql_check_group_beneficiary_crud: specifies whether Group Beneficiary should use tasks based approval (default: True),


## openIMIS Modules Dependencies
- core
- individual

## OpenSearch

### Available Documents 
* BeneficiaryDocument

### How to initlaize data after deployment
* If you have initialized the application but still have some data to be transferred, you can effortlessly 
achieve this by using the commands available in this module: `python manage.py add_beneficiary_data_to_opensearch`. 
This command loads existing data into OpenSearch.

### How to Import a Dashboard
* Locate the dashboard definition file in `.ndjson` format within 
the `openimis-be_social_protection/import_data` directory.
* Log in to your OpenSearch instance.
* Expand the sidebar located on the left side of the page.
* Navigate to `Management` and select `Dashboards Management`.
* On the left side of the page, click on `Saved Objects`.
* At the top-right corner of the table, click on `Import`.
* A new side-modal will appear on the right side of the page. 
Drag and drop the file from `openimis-be_social_protection/import_data` into the import dropzone.
* This action will import the dashboards along with related 
charts that should be accessible on the visualization page.
* Verify if the dashboards have been imported properly.

### File for importing in .ndsjon format
* This file contains dashboard definitions that can be easily uploaded, as described in the "How to Import a Dashboard" 
section above. It includes definitions of dashboards and the visualizations contained within them.

### How to Export Dashboards with Related Objects like Visualizations in OpenSearch?
* Log in to your OpenSearch instance.
* Expand the sidebar located on the left side of the page.
* Navigate to `Management` and select `Dashboards Management`.
* On the left side of the page, click on `Saved Objects`.
* At the top-right corner of the table, click on `Export <N> objects`.
* Ensure that you have selected dashboards only. Additionally, choose the option to 
include related objects, and then click export all.
* You should have downloaded file in `.ndjson` format. 
* Save file in the business model for initialization after deployment in 
`openimis-be_social_protection/import_data`.
* Rename filename into `opensearch_beneficiary_dashboard.ndjson`
