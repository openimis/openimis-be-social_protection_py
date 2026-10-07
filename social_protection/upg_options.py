"""Phase-specific UPG UI options, also enforced by enrollment execution."""
import json
from django.core.exceptions import ValidationError


def upg_gender_options(plan):
    config = plan.json_ext or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except ValueError as exc:
            raise ValidationError("Phase json_ext must be valid JSON.") from exc
    if not isinstance(config, dict):
        raise ValidationError("Phase json_ext must be an object.")
    options = config.get("upg_head_gender_options", ["FEMALE", "MALE"])
    if (not isinstance(options, list) or not options
            or any(value not in ("FEMALE", "MALE", "BOTH") for value in options)
            or len(set(options)) != len(options)):
        raise ValidationError("upg_head_gender_options must contain unique FEMALE, MALE or BOTH options.")
    return options
