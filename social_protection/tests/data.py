service_add_payload = {
    "code": "example",
    "name": "example_name",
    "maxBeneficiaries": 0,
    "ceilingPerBeneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "dateValidFrom": "2023-01-01",
    "dateValidTo": "2023-12-31",
    "jsonExt": "{\"key\":\"value\"}"
}

service_add_payload_same_code = {
    "code": "example",
    "name": "random",
    "maxBeneficiaries": 0,
    "ceilingPerBeneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "dateValidFrom": "2023-01-01",
    "dateValidTo": "2023-12-31",
    "jsonExt": "{\"key\":\"value\"}"
}

service_add_payload_same_name = {
    "code": "random",
    "name": "example_name",
    "maxBeneficiaries": 0,
    "ceilingPerBeneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "dateValidFrom": "2023-01-01",
    "dateValidTo": "2023-12-31",
    "jsonExt": "{\"key\":\"value\"}"
}

service_add_payload_invalid_schema = {
    "code": "random",
    "name": "example_name",
    "maxBeneficiaries": 0,
    "ceilingPerBeneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema",
        "type": "object",
        "properties": {
            "invalid_property": {
                "type": "string"
            }
        },
        "required": ["invalid_property"]
    },
    "dateValidFrom": "2023-01-01",
    "dateValidTo": "2023-12-31",
    "jsonExt": "{\"key\":\"value\"}"
}

service_add_payload_no_ext = {
    "code": "example",
    "name": "example_name",
    "maxBeneficiaries": 0,
    "ceilingPerBeneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "dateValidFrom": "2023-01-01",
    "dateValidTo": "2023-12-31",
}

service_update_payload = {
    "code": "update",
    "name": "example_update",
    "maxBeneficiaries": 0,
    "ceilingPerBeneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "dateValidFrom": "2023-01-01",
    "dateValidTo": "2023-12-31",
    "jsonExt": "{\"key\":\"updated_value\"}"
}

service_beneficiary_add_payload = {
    "status": "Potential",
    "dateValidFrom": "2023-01-01",
    "dateValidTo": "2023-12-31",
    "jsonExt": "{\"key\":\"value\"}"
}

service_beneficiary_update_payload = {
    "status": "Active",
    "dateValidFrom": "2023-01-01",
    "dateValidTo": "2023-12-31",
    "jsonExt": "{\"key\":\"value\"}"
}
