service_add_payload = {
    "code": "example",
    "name": "example_name",
    "max_beneficiaries": 0,
    "ceiling_per_beneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "date_valid_from": "2023-01-01",
    "date_valid_to": "2023-12-31",
}

service_add_payload_same_code = {
    "code": "example",
    "name": "random",
    "max_beneficiaries": 0,
    "ceiling_per_beneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "date_valid_from": "2023-01-01",
    "date_valid_to": "2023-12-31",
}

service_add_payload_same_name = {
    "code": "random",
    "name": "example_name",
    "max_beneficiaries": 0,
    "ceiling_per_beneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "date_valid_from": "2023-01-01",
    "date_valid_to": "2023-12-31",
}

service_add_payload_invalid_schema = {
    "code": "random",
    "name": "example_name",
    "max_beneficiaries": 0,
    "ceiling_per_beneficiary": "0.00",
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
    "date_valid_from": "2023-01-01",
    "date_valid_to": "2023-12-31",
}

service_add_payload_no_ext = {
    "code": "example",
    "name": "example_name",
    "max_beneficiaries": 0,
    "ceiling_per_beneficiary": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "date_valid_from": "2023-01-01",
    "date_valid_to": "2023-12-31",
}

service_update_payload = {
    "code": "update",
    "name": "example_update",
    "max_beneficiaries": 0,
    "ceiling_per_beneficiaryd": "0.00",
    "beneficiary_data_schema": {
        "$schema": "https://json-schema.org/draft/2019-09/schema"
    },
    "date_valid_from": "2023-01-01",
    "date_valid_to": "2023-12-31",
}

service_beneficiary_add_payload = {
    "status": "Potential",
    "date_valid_from": "2023-01-01",
    "date_valid_to": "2023-12-31",
}

service_beneficiary_update_payload = {
    "status": "Active",
    "date_valid_from": "2023-01-01",
    "date_valid_to": "2023-12-31",
}
