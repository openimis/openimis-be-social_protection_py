"""Validated phase-level UPG criteria; absent configuration preserves legacy behavior."""
import json
from django.core.exceptions import ValidationError


DEFAULTS = {
    "previous_programme": "SCTP",
    "enrollment_status": None,
    "participant_status": "YES",
    "member_min_age": 18,
    "member_max_age": 64,
    "requires_livelihood_activity": False,
    "validation_statuses": [],
}


def upg_criteria(plan):
    config = plan.json_ext or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except ValueError as exc:
            raise ValidationError("Phase json_ext must be valid JSON.") from exc
    if not isinstance(config, dict):
        raise ValidationError("Phase json_ext must be an object.")
    raw = config.get("upg_criteria", {})
    if not isinstance(raw, dict) or set(raw) - set(DEFAULTS):
        raise ValidationError("upg_criteria must be an object containing only supported criteria keys.")
    result = {**DEFAULTS, **raw}
    if not isinstance(result['previous_programme'], str) or not result['previous_programme'].strip():
        raise ValidationError("previous_programme must be a nonempty programme code or name.")
    if result['enrollment_status'] not in (None, 'ACTIVE', 'POTENTIAL', 'SUSPENDED', 'GRADUATED'):
        raise ValidationError("Invalid UPG enrollment_status.")
    if result['participant_status'] is not None and (
        not isinstance(result['participant_status'], str) or not result['participant_status'].strip()
    ):
        raise ValidationError("participant_status must be a nonempty string or null.")
    low, high = result['member_min_age'], result['member_max_age']
    if type(low) is not int or type(high) is not int or not 0 <= low <= high <= 120:
        raise ValidationError("UPG member ages must be integers with 0 <= minimum <= maximum <= 120.")
    if type(result['requires_livelihood_activity']) is not bool:
        raise ValidationError("requires_livelihood_activity must be boolean.")
    statuses = result['validation_statuses']
    if not isinstance(statuses, list) or any(s not in ('VERIFIED', 'NOT_VERIFIED') for s in statuses):
        raise ValidationError("validation_statuses must be a list of VERIFIED and/or NOT_VERIFIED.")
    return result
