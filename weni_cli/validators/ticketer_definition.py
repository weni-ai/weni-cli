import re
from typing import Any, Optional

from weni_cli.validators.channel_definition import load_yaml_file

# Constants for ticketer validation
MAX_TICKETER_NAME_LENGTH = 100
AVAILABLE_TICKETER_TYPES = ["generic"]

REQUIRED_CONFIG_FIELDS = ["base_url", "api_token"]

OPTIONAL_CONFIG_FIELDS = [
    "skip_webhook_hmac",
    "project_uuid",
    "project_name",
    "route_open",
    "route_forward",
    "route_close",
    "route_reopen",
    "route_history",
    "webhook_secret",
]

URL_PATTERN = re.compile(r"^https?://")


def skip_webhook_hmac_enabled(value: str) -> bool:
    """Return True when skip_webhook_hmac disables HMAC verification."""
    normalized = value.strip().lower()
    return normalized in ("true", "1", "yes")


def validate_ticketer_definition_schema(data):
    """
    Validates that the ticketer definition YAML contains all required fields and has a valid structure.

    Args:
        data (dict): Parsed YAML data

    Returns:
        str | None: Error message if validation fails, None otherwise
    """
    if data.get("ticketers") is None:
        return "Missing required root key 'ticketers' in the ticketer definition file"

    if not isinstance(data["ticketers"], list):
        return "'ticketers' must be an array in the ticketer definition file"

    if not data["ticketers"]:
        return "No ticketers defined in the ticketer definition file"

    for ticketer_idx, ticketer_data in enumerate(data["ticketers"]):
        if not isinstance(ticketer_data, dict):
            return f"Ticketer at index {ticketer_idx} must be an object in the ticketer definition file"

        if not ticketer_data.get("name"):
            return (
                f"Ticketer at index {ticketer_idx} is missing required field 'name' "
                "in the ticketer definition file"
            )
        if not isinstance(ticketer_data["name"], str):
            return (
                f"Ticketer at index {ticketer_idx}: 'name' must be a string "
                "in the ticketer definition file"
            )
        if len(ticketer_data["name"]) > MAX_TICKETER_NAME_LENGTH:
            return (
                f"Ticketer at index {ticketer_idx}: 'name' must be less than "
                f"{MAX_TICKETER_NAME_LENGTH} characters in the ticketer definition file"
            )

        if not ticketer_data.get("ticketer_type"):
            return (
                f"Ticketer at index {ticketer_idx} is missing required field 'ticketer_type' "
                "in the ticketer definition file"
            )
        if not isinstance(ticketer_data["ticketer_type"], str):
            return (
                f"Ticketer at index {ticketer_idx}: 'ticketer_type' must be a string "
                "in the ticketer definition file"
            )
        if ticketer_data["ticketer_type"] not in AVAILABLE_TICKETER_TYPES:
            return (
                f"Ticketer at index {ticketer_idx}: 'ticketer_type' must be one of: "
                f"{', '.join(AVAILABLE_TICKETER_TYPES)} in the ticketer definition file"
            )

        if not ticketer_data.get("config"):
            return (
                f"Ticketer at index {ticketer_idx} is missing required field 'config' "
                "in the ticketer definition file"
            )
        if not isinstance(ticketer_data["config"], dict):
            return (
                f"Ticketer at index {ticketer_idx}: 'config' must be an object "
                "in the ticketer definition file"
            )

        config = ticketer_data["config"]
        allowed_fields = set(REQUIRED_CONFIG_FIELDS + OPTIONAL_CONFIG_FIELDS)

        for field in REQUIRED_CONFIG_FIELDS:
            if field not in config:
                return (
                    f"Ticketer at index {ticketer_idx}: 'config' is missing required field "
                    f"'{field}' in the ticketer definition file"
                )

        for field, value in config.items():
            if field not in allowed_fields:
                return (
                    f"Ticketer at index {ticketer_idx}: 'config.{field}' is not a recognized "
                    "field in the ticketer definition file"
                )
            if not isinstance(value, str):
                return (
                    f"Ticketer at index {ticketer_idx}: 'config.{field}' must be a string "
                    "in the ticketer definition file"
                )

        if not config["base_url"].strip():
            return (
                f"Ticketer at index {ticketer_idx}: 'config.base_url' must not be empty "
                "in the ticketer definition file"
            )
        if not URL_PATTERN.match(config["base_url"].strip()):
            return (
                f"Ticketer at index {ticketer_idx}: 'config.base_url' must be a valid URL "
                "starting with http:// or https:// in the ticketer definition file"
            )

        if not config["api_token"].strip():
            return (
                f"Ticketer at index {ticketer_idx}: 'config.api_token' must not be empty "
                "in the ticketer definition file"
            )

        skip_hmac = skip_webhook_hmac_enabled(config.get("skip_webhook_hmac", ""))
        webhook_secret = config.get("webhook_secret", "").strip()
        if not skip_hmac and not webhook_secret:
            return (
                f"Ticketer at index {ticketer_idx}: 'config.webhook_secret' is required unless "
                "'config.skip_webhook_hmac' is set to true, 1 or yes in the ticketer definition file"
            )

        for field in OPTIONAL_CONFIG_FIELDS:
            if field in config and field != "skip_webhook_hmac" and not config[field].strip():
                if field == "webhook_secret" and skip_hmac:
                    continue
                if field in ("project_uuid", "project_name") and config[field] == "":
                    continue
                return (
                    f"Ticketer at index {ticketer_idx}: 'config.{field}' must not be empty "
                    "in the ticketer definition file"
                )

    return None


def load_ticketer_definition(path) -> tuple[Any, Optional[Exception]]:
    """
    Loads a ticketer definition from a YAML file.

    Args:
        path (str): Path to the ticketer definition file

    Returns:
        tuple: (parsed_data, error) where error is None if successful
    """
    data, error = load_yaml_file(path)
    if error:
        return None, error

    if not data:
        return None, Exception("Empty definition file")

    return data, None
