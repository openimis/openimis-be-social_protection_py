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
