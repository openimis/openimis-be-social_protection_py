import logging

# from social_protection.workflows.utils import validate_dataframe_headers, load_df, \
#     create_task_or_execute_sql
from social_protection.workflows.utils import SqlProcedurePythonWorkflow

logger = logging.getLogger(__name__)


def process_import_valid_beneficiaries_workflow(user_uuid, benefit_plan_uuid, upload_uuid, accepted=None):
    service = SqlProcedurePythonWorkflow(benefit_plan_uuid, upload_uuid, user_uuid, accepted)
    service.validate_dataframe_headers()
    if isinstance(accepted, list):
        service.execute(upload_sql_partial, [upload_uuid, user_uuid, benefit_plan_uuid, accepted])
    else:
        service.execute(upload_sql, [upload_uuid, user_uuid, benefit_plan_uuid])


upload_sql = """
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
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND NOT "Json_ext" ? 'first_name';

    SELECT ARRAY_AGG("UUID") INTO failing_entries_last_name
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND NOT "Json_ext" ? 'last_name';

    SELECT ARRAY_AGG("UUID") INTO failing_entries_dob
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND NOT "Json_ext" ? 'dob';

    -- Check if any entries have invalid Json_ext according to the schema
    SELECT beneficiary_data_schema INTO json_schema FROM social_protection_benefitplan WHERE "UUID" = benefitPlan;
    SELECT ARRAY_AGG("UUID") INTO failing_entries_invalid_json
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND NOT validate_json_schema(json_schema, "Json_ext");

    -- If any entries do not meet the criteria or missing required fields, set the error message in the upload table and do not proceed further
    IF failing_entries_invalid_json IS NOT NULL OR failing_entries_first_name IS NOT NULL OR failing_entries_last_name IS NOT NULL OR failing_entries_dob IS NOT NULL THEN
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
        
        UPDATE individual_individualdatasourceupload SET status = 'FAIL' WHERE "UUID" = current_upload_id;
    ELSE
        -- If no invalid entries, then proceed with the data manipulation
        WITH new_entry AS (
            INSERT INTO individual_individual(
                "UUID", "isDeleted", version, "UserCreatedUUID", "UserUpdatedUUID",
                "Json_ext", first_name, last_name, dob
            )
            SELECT gen_random_uuid(), false, 1, userUUID, userUUID,
                   "Json_ext", "Json_ext"->>'first_name', "Json_ext" ->> 'last_name', to_date("Json_ext" ->> 'dob', 'YYYY-MM-DD')
            FROM individual_individualdatasource
            WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND validations ->> 'validation_errors' = '[]'
            RETURNING "UUID", "Json_ext"
        )
        UPDATE individual_individualdatasource
        SET individual_id = ne."UUID"
        FROM new_entry ne
        WHERE individual_individualdatasource.upload_id = current_upload_id
          AND individual_individualdatasource.individual_id IS NULL
          AND individual_individualdatasource."isDeleted" = False
          AND individual_individualdatasource."Json_ext" = ne."Json_ext"
          AND validations ->> 'validation_errors' = '[]';
        
        with new_entry_2 as (INSERT INTO social_protection_beneficiary(
        "UUID", "isDeleted", "Json_ext", "DateCreated", "DateUpdated", version, "DateValidFrom", "DateValidTo", status, "benefit_plan_id", "individual_id", "UserCreatedUUID", "UserUpdatedUUID"
        )
        SELECT gen_random_uuid(), false, iids."Json_ext" - 'first_name' - 'last_name' - 'dob', NOW(), NOW(), 1, NOW(), NULL, 'POTENTIAL', benefitPlan, new_entry."UUID", userUUID, userUUID
        FROM individual_individualdatasource iids right join individual_individual new_entry on new_entry."UUID" = iids.individual_id
        WHERE iids.upload_id=current_upload_id and iids."isDeleted"=false
        returning "UUID")
        
        -- Change status to SUCCESS if no invalid items, change to PARTIAL_SUCCESS otherwise 
            UPDATE individual_individualdatasourceupload
            SET 
                status = CASE
                    WHEN (
                        SELECT count(*) 
                        FROM individual_individualdatasource
                        WHERE upload_id=current_upload_id
                            AND "isDeleted"=FALSE
                            AND validations ->> 'validation_errors' = '[]'
                    ) = (
                        SELECT count(*) 
                        FROM individual_individualdatasource
                        WHERE upload_id=current_upload_id
                            AND "isDeleted"=FALSE
                    ) THEN 'SUCCESS'
                    ELSE 'PARTIAL_SUCCESS'
                END,
                error = '{}'
            WHERE "UUID" = current_upload_id;
    END IF;
EXCEPTION WHEN OTHERS THEN
    UPDATE individual_individualdatasourceupload SET status = 'FAIL', error = jsonb_build_object(
        'error', SQLERRM,
        'timestamp', NOW()::text,
        'upload_id', current_upload_id::text
    )
    WHERE "UUID" = current_upload_id;
END $$;

"""

upload_sql_partial = """
DO $$
DECLARE
    current_upload_id UUID := %s::UUID;
    userUUID UUID := %s::UUID;
    benefitPlan UUID := %s::UUID;
    accepted UUID[] := %s::UUID[]; -- Placeholder for the accepted UUIDs array, can be NULL
    failing_entries UUID[];
    json_schema jsonb;
    failing_entries_invalid_json UUID[];
    failing_entries_first_name UUID[];
    failing_entries_last_name UUID[];
    failing_entries_dob UUID[];
BEGIN
    -- Check if all required fields are present in the entries, with accepted filter applied if not NULL
    SELECT ARRAY_AGG("UUID") INTO failing_entries_first_name
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND NOT "Json_ext" ? 'first_name'
    AND (accepted IS NULL OR "UUID" = ANY(accepted));

    SELECT ARRAY_AGG("UUID") INTO failing_entries_last_name
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND NOT "Json_ext" ? 'last_name'
    AND (accepted IS NULL OR "UUID" = ANY(accepted));

    SELECT ARRAY_AGG("UUID") INTO failing_entries_dob
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND NOT "Json_ext" ? 'dob'
    AND (accepted IS NULL OR "UUID" = ANY(accepted));

    -- Check if any entries have invalid Json_ext according to the schema, with accepted filter applied if not NULL
    SELECT ARRAY_AGG("UUID") INTO failing_entries_invalid_json
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND NOT validate_json_schema(json_schema, "Json_ext")
    AND (accepted IS NULL OR "UUID" = ANY(accepted));

    -- If any entries do not meet the criteria or missing required fields, set the error message in the upload table and do not proceed further
    IF failing_entries_invalid_json IS NOT NULL OR failing_entries_first_name IS NOT NULL OR failing_entries_last_name IS NOT NULL OR failing_entries_dob IS NOT NULL THEN
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
        
        UPDATE individual_individualdatasourceupload SET status = 'FAIL' WHERE "UUID" = current_upload_id;
    ELSE
        -- If no invalid entries, then proceed with the data manipulation, considering the accepted filter
        WITH new_entry AS (
            INSERT INTO individual_individual(
                "UUID", "isDeleted", version, "UserCreatedUUID", "UserUpdatedUUID",
                "Json_ext", first_name, last_name, dob
            )
            SELECT gen_random_uuid(), false, 1, userUUID, userUUID,
                   "Json_ext", "Json_ext"->>'first_name', "Json_ext" ->> 'last_name', to_date("Json_ext" ->> 'dob', 'YYYY-MM-DD')
            FROM individual_individualdatasource
            WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = False AND validations ->> 'validation_errors' = '[]'
            AND (accepted IS NULL OR "UUID" = ANY(accepted))
            RETURNING "UUID", "Json_ext"
        )
        UPDATE individual_individualdatasource
        SET individual_id = ne."UUID"
        FROM new_entry ne
        WHERE individual_individualdatasource.upload_id = current_upload_id
          AND individual_individualdatasource.individual_id IS NULL
          AND individual_individualdatasource."isDeleted" = False
          AND individual_individualdatasource."Json_ext" = ne."Json_ext"
          AND validations ->> 'validation_errors' = '[]'
          AND (accepted IS NULL OR individual_individualdatasource."UUID" = ANY(accepted));
        
        WITH new_entry_2 AS (
            INSERT INTO social_protection_beneficiary(
                "UUID", "isDeleted", "Json_ext", "DateCreated", "DateUpdated", version, "DateValidFrom", "DateValidTo", status, "benefit_plan_id", "individual_id", "UserCreatedUUID", "UserUpdatedUUID"
            )
            SELECT gen_random_uuid(), false, iids."Json_ext" - 'first_name' - 'last_name' - 'dob', NOW(), NOW(), 1, NOW(), NULL, 'POTENTIAL', benefitPlan, new_entry."UUID", userUUID, userUUID
            FROM individual_individualdatasource iids
            JOIN new_entry ON new_entry."UUID" = iids.individual_id
            WHERE iids.upload_id = current_upload_id AND iids."isDeleted" = false AND iids."UUID" = ANY(accepted)
            RETURNING "UUID"
        ) select null;
    END IF;
EXCEPTION WHEN OTHERS THEN
    UPDATE individual_individualdatasourceupload SET status = 'FAIL', error = jsonb_build_object(
        'error', SQLERRM,
        'timestamp', NOW()::text,
        'upload_id', current_upload_id::text
    )
    WHERE "UUID" = current_upload_id;
END $$;

"""