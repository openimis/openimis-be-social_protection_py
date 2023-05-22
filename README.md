# openIMIS Backend social_protection reference module
This repository holds the files of the openIMIS Backend social_protection reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

## ORM mapping:
* tblBenefitPlan > BenefitPlan

## GraphQl Queries
* benefitPlan

## GraphQL Mutations - each mutation emits default signals and return standard error lists (cfr. openimis-be-core_py)
* createBenefitPlan
* updateBenefitPlan
* deleteBenefitPlan

## Services
- BenefitPlan
  - create
  - update
  - delete

## Configuration options (can be changed via core.ModuleConfiguration)
* gql_benefit_plan_search_perms: required rights to call benefitPlan GraphQL Query (default: ["160001"])
* gql_benefit_plan_create_perms: required rights to call createBenefitPlan GraphQL Mutation (default: ["160002"])
* gql_benefit_plan_update_perms: required rights to call updateBenefitPlan GraphQL Mutation (default: ["160003"])
* gql_benefit_plan_delete_perms: required rights to call deleteBenefitPlan GraphQL Mutation (default: ["160004"])


## openIMIS Modules Dependencies
- core
- policyholder