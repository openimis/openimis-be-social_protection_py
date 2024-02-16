import json
import logging

from django.db import connection
from django.db import ProgrammingError

from core.models import User
from individual.models import IndividualDataSource
from social_protection.models import BenefitPlan
from social_protection.services import BeneficiaryImportService
from social_protection.utils import load_dataframe
from workflow.exceptions import PythonWorkflowHandlerException

logger = logging.getLogger(__name__)


def validate_dataframe_headers(df, schema):
    """
    Validates if DataFrame headers:
    1. Are included in the JSON schema properties.
    2. Include 'first_name', 'last_name', and 'dob'.
    """
    df_headers = set(df.columns)
    schema_properties = set(schema.get('properties', {}).keys())
    required_headers = {'first_name', 'last_name', 'dob', 'id'}

    errors = []
    if not (df_headers-required_headers).issubset(schema_properties):
        invalid_headers = df_headers - schema_properties - required_headers
        errors.append(
            F"Uploaded beneficiaries contains invalid columns: {invalid_headers}"
        )

    for field in required_headers:
        if field not in df_headers:
            errors.append(
                F"Uploaded beneficiaries missing essential header: {field}"
            )

    if errors:
        raise PythonWorkflowHandlerException("\n".join(errors))


def process_import_beneficiaries_workflow(user_uuid, benefit_plan_uuid, upload_uuid):
    # Call the records validation service directly with the provided arguments
    user = User.objects.get(id=user_uuid)
    import_service = BeneficiaryImportService(user)
    benefit_plan = BenefitPlan.objects.filter(uuid=benefit_plan_uuid, is_deleted=False).first()
    schema = benefit_plan.beneficiary_data_schema
    df = load_dataframe(IndividualDataSource.objects.filter(upload_id=upload_uuid))

    # Valid headers are necessary conditions, breaking whole update. If file is invalid then
    # upload is aborted because no record can be uploaded.
    validate_dataframe_headers(df, schema)

    validation_response = import_service.validate_import_beneficiaries(
        upload_id=upload_uuid,
        individual_sources=IndividualDataSource.objects.filter(upload_id=upload_uuid),
        benefit_plan=benefit_plan
    )

    try:
        if validation_response['summary_invalid_items']:
            # If some records were not validated, call the task creation service
            import_service.create_task_with_importing_valid_items(upload_uuid, benefit_plan)
        else:
            # All records are fine, execute SQL logic
            execute_sql_logic(upload_uuid, user_uuid, benefit_plan_uuid)
    except ProgrammingError as e:
        # The exception on procedure execution is handled by the procedure itself.
        logger.log(logging.WARNING, F'Error during beneficiary upload workflow, details:\n{str(e)}')
        return
    except Exception as e:
        raise PythonWorkflowHandlerException(str(e))


def execute_sql_logic(upload_uuid, user_uuid, benefit_plan_uuid):
    with connection.cursor() as cursor:
        current_upload_id = upload_uuid
        userUUID = user_uuid
        benefitPlan = benefit_plan_uuid
        # The SQL logic here needs to be carefully translated or executed directly
        # The provided SQL is complex and may require breaking down into multiple steps or ORM operations
        cursor.execute("""
DO $$
 DECLARE
            current_upload_id UUID := %s::UUID;
            userUUID UUID := %s::UUID;
            benefitPlan UUID := %s::UUID;
            failing_entries UUID[];
            json_schema jsonb;
            failing_entries_invalid_json UUID[];
            failing_entries_first_name UUID[];
            failing_entries_last_name UUID[];
            failing_entries_dob UUID[];
            BEGIN
    -- Check if all required fields are present in the entries
    SELECT ARRAY_AGG("UUID") INTO failing_entries_first_name
    FROM individual_individualdatasource
    WHERE upload_id=current_upload_id and individual_id is null and "isDeleted"=False AND NOT "Json_ext" ? 'first_name';

    SELECT ARRAY_AGG("UUID") INTO failing_entries_last_name
    FROM individual_individualdatasource
    WHERE upload_id=current_upload_id and individual_id is null and "isDeleted"=False AND NOT "Json_ext" ? 'last_name';

    SELECT ARRAY_AGG("UUID") INTO failing_entries_dob
    FROM individual_individualdatasource
    WHERE upload_id=current_upload_id and individual_id is null and "isDeleted"=False AND NOT "Json_ext" ? 'dob';


    -- Check if any entries have invalid Json_ext according to the schema
    SELECT beneficiary_data_schema INTO json_schema FROM social_protection_benefitplan WHERE "UUID" = benefitPlan;
    SELECT ARRAY_AGG("UUID") INTO failing_entries_invalid_json
    FROM individual_individualdatasource
    WHERE upload_id=current_upload_id and individual_id is null and "isDeleted"=False AND NOT validate_json_schema(json_schema, "Json_ext");

    -- If any entries do not meet the criteria or missing required fields, set the error message in the upload table and do not proceed further
    IF failing_entries_invalid_json IS NOT NULL or failing_entries_first_name IS NOT NULL OR failing_entries_last_name IS NOT NULL OR failing_entries_dob IS NOT NULL THEN
        UPDATE individual_individualdatasourceupload
        SET error = coalesce(error, '{}'::jsonb) || jsonb_build_object('errors', jsonb_build_object(
                            'error', 'Invalid entries',
                            'timestamp', NOW()::text,
                            'upload_id', current_upload_id::text,
                            'failing_entries_first_name', failing_entries_first_name,
                            'failing_entries_last_name', failing_entries_last_name,
                            'failing_entries_dob', failing_entries_dob,
                            'failing_entries_invalid_json', failing_entries_invalid_json
                        ))
        WHERE "UUID" = current_upload_id;

       update individual_individualdatasourceupload set status='FAIL' where "UUID" = current_upload_id;
    -- If no invalid entries, then proceed with the data manipulation
    ELSE
        BEGIN
          WITH new_entry AS (
            INSERT INTO individual_individual(
            "UUID", "isDeleted", version, "UserCreatedUUID", "UserUpdatedUUID",
            "Json_ext", first_name, last_name, dob
            )
            SELECT gen_random_uuid(), false, 1, userUUID, userUUID,
            "Json_ext", "Json_ext"->>'first_name', "Json_ext" ->> 'last_name', to_date("Json_ext" ->> 'dob', 'YYYY-MM-DD')
            FROM individual_individualdatasource
            WHERE upload_id=current_upload_id and individual_id is null and "isDeleted"=False
            RETURNING "UUID", "Json_ext"  -- also return the Json_ext
          )
          UPDATE individual_individualdatasource
          SET individual_id = new_entry."UUID"
          FROM new_entry
          WHERE upload_id=current_upload_id
            and individual_id is null
            and "isDeleted"=False
            and individual_individualdatasource."Json_ext" = new_entry."Json_ext";  -- match on Json_ext


            with new_entry_2 as (INSERT INTO social_protection_beneficiary(
            "UUID", "isDeleted", "Json_ext", "DateCreated", "DateUpdated", version, "DateValidFrom", "DateValidTo", status, "benefit_plan_id", "individual_id", "UserCreatedUUID", "UserUpdatedUUID"
            )
            SELECT gen_random_uuid(), false, iids."Json_ext" - 'first_name' - 'last_name' - 'dob', NOW(), NOW(), 1, NOW(), NULL, 'POTENTIAL', benefitPlan, new_entry."UUID", userUUID, userUUID
            FROM individual_individualdatasource iids right join individual_individual new_entry on new_entry."UUID" = iids.individual_id
            WHERE iids.upload_id=current_upload_id and iids."isDeleted"=false
            returning "UUID")


            update individual_individualdatasourceupload set status='SUCCESS', error='{}' where "UUID" = current_upload_id;
            EXCEPTION
            WHEN OTHERS then

            update individual_individualdatasourceupload set status='FAIL' where "UUID" = current_upload_id;
                UPDATE individual_individualdatasourceupload
                SET error = coalesce(error, '{}'::jsonb) || jsonb_build_object('errors', jsonb_build_object(
                                    'error', SQLERRM,
                                    'timestamp', NOW()::text,
                                    'upload_id', current_upload_id::text
                                ))
                WHERE "UUID" = current_upload_id;
        END;
    END IF;
END $$;
        """, [current_upload_id, userUUID, benefitPlan])
        # Process the cursor results or handle exceptions
