import json
import re
from typing import Any, Optional

from weni_cli.validators.channel_definition import load_yaml_file

# Constants for ticketer validation
MAX_TICKETER_NAME_LENGTH = 100
AVAILABLE_TICKETER_TYPES = ["generic"]
TOKEN_REFRESH_TYPES = ["custom", "refresh"]
TOKEN_REFRESH_CONFIG_FIELD = "token_refresh_config"
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1
FORM_URLENCODED = "application/x-www-form-urlencoded"

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
    "route_history_message",
    "webhook_secret",
    "history_mode",
    "history_batch_size",
    # Plataforma → Ticketer (request/response body templates)
    "open_template",
    "open_response_template",
    "forward_template",
    "forward_response_template",
    "close_template",
    "close_response_template",
    "history_template",
    "history_response_template",
    # Ticketer → Plataforma (inbound webhook request/response templates)
    "messages_template",
    "messages_response_template",
    "tickets_close_template",
    "tickets_close_response_template",
    # Platform → Ticketer OAuth2 token refresh (Mailroom generic ticketer)
    "token_refresh_enabled",
    "token_refresh_type",
    "token_refresh_config",
    "refresh_token",
    "expires_in",
    "client_id",
    "client_secret",
]

URL_PATTERN = re.compile(r"^https?://")


def skip_webhook_hmac_enabled(value: str) -> bool:
    """Return True when skip_webhook_hmac disables HMAC verification."""
    return _truthy_config_flag(value)


def token_refresh_enabled(value: str) -> bool:
    """Return True when token refresh is turned on."""
    return _truthy_config_flag(value)


def _truthy_config_flag(value: str) -> bool:
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
                f"Ticketer at index {ticketer_idx} is missing required field 'name' " "in the ticketer definition file"
            )
        if not isinstance(ticketer_data["name"], str):
            return f"Ticketer at index {ticketer_idx}: 'name' must be a string " "in the ticketer definition file"
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
            return f"Ticketer at index {ticketer_idx}: 'config' must be an object " "in the ticketer definition file"

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
            if field == TOKEN_REFRESH_CONFIG_FIELD:
                if not isinstance(value, (str, dict)):
                    return (
                        f"Ticketer at index {ticketer_idx}: 'config.{field}' must be a JSON string "
                        "or object in the ticketer definition file"
                    )
                continue
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
            if field not in config or field in ("skip_webhook_hmac", TOKEN_REFRESH_CONFIG_FIELD):
                continue
            if not config[field].strip():
                if field == "webhook_secret" and skip_hmac:
                    continue
                if field in ("project_uuid", "project_name") and config[field] == "":
                    continue
                return (
                    f"Ticketer at index {ticketer_idx}: 'config.{field}' must not be empty "
                    "in the ticketer definition file"
                )

        refresh_error = _validate_and_serialize_token_refresh(config, ticketer_idx)
        if refresh_error:
            return refresh_error

    return None


def _validate_and_serialize_token_refresh(config: dict, ticketer_idx: int) -> Optional[str]:
    expires_in = config.get("expires_in")
    if expires_in is not None:
        expires_error = _validate_int64_string(expires_in, ticketer_idx, "expires_in")
        if expires_error:
            return expires_error

    if not token_refresh_enabled(config.get("token_refresh_enabled", "")):
        if TOKEN_REFRESH_CONFIG_FIELD in config:
            serialize_error = _serialize_token_refresh_config(config, ticketer_idx, strip_body=False)
            if serialize_error:
                return serialize_error
        return None

    refresh_type = config.get("token_refresh_type", "").strip().lower()
    if refresh_type not in TOKEN_REFRESH_TYPES:
        return (
            f"Ticketer at index {ticketer_idx}: 'config.token_refresh_type' is required when "
            "token refresh is enabled and must be 'custom' or 'refresh' in the ticketer definition file"
        )
    config["token_refresh_type"] = refresh_type

    if TOKEN_REFRESH_CONFIG_FIELD not in config:
        return (
            f"Ticketer at index {ticketer_idx}: 'config.token_refresh_config' is required "
            "when token refresh is enabled in the ticketer definition file"
        )

    parsed, parse_error = _parse_token_refresh_config(config[TOKEN_REFRESH_CONFIG_FIELD], ticketer_idx)
    if parse_error or parsed is None:
        return parse_error

    url = parsed.get("url")
    if not isinstance(url, str) or not url.strip():
        return (
            f"Ticketer at index {ticketer_idx}: 'config.token_refresh_config.url' is required "
            "when token refresh is enabled in the ticketer definition file"
        )

    when = parsed.get("when")
    if when is not None:
        if not isinstance(when, dict):
            return (
                f"Ticketer at index {ticketer_idx}: 'config.token_refresh_config.when' must be an object "
                "in the ticketer definition file"
            )
        match = when.get("match")
        if match is not None and str(match).strip() != "" and str(match).strip().lower() != "any":
            return (
                f"Ticketer at index {ticketer_idx}: 'config.token_refresh_config.when.match' must be 'any' "
                "in the ticketer definition file"
            )

    if refresh_type == "custom":
        body = parsed.get("body")
        if not isinstance(body, str) or not body.strip():
            return (
                f"Ticketer at index {ticketer_idx}: 'config.token_refresh_config.body' is required "
                "when token_refresh_type is 'custom' in the ticketer definition file"
            )
    else:
        refresh_token = config.get("refresh_token", "").strip()
        if not refresh_token:
            return (
                f"Ticketer at index {ticketer_idx}: 'config.refresh_token' is required when "
                "token_refresh_type is 'refresh' in the ticketer definition file"
            )
        parsed.pop("body", None)
        _ensure_form_urlencoded_header(parsed)

    headers = parsed.get("headers")
    if headers is not None:
        if not isinstance(headers, dict) or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()
        ):
            return (
                f"Ticketer at index {ticketer_idx}: 'config.token_refresh_config.headers' must be "
                "a map of strings in the ticketer definition file"
            )

    config[TOKEN_REFRESH_CONFIG_FIELD] = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
    return None


def _parse_token_refresh_config(value: Any, ticketer_idx: int) -> tuple[Optional[dict], Optional[str]]:
    invalid_json = (
        f"Ticketer at index {ticketer_idx}: 'config.token_refresh_config' must be valid JSON "
        "in the ticketer definition file"
    )
    if isinstance(value, dict):
        return dict(value), None
    if not isinstance(value, str):
        return None, invalid_json
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None, invalid_json
    if not isinstance(parsed, dict):
        return None, invalid_json
    return parsed, None


def _serialize_token_refresh_config(config: dict, ticketer_idx: int, strip_body: bool) -> Optional[str]:
    parsed, parse_error = _parse_token_refresh_config(config[TOKEN_REFRESH_CONFIG_FIELD], ticketer_idx)
    if parse_error or parsed is None:
        return parse_error
    if strip_body:
        parsed.pop("body", None)
    config[TOKEN_REFRESH_CONFIG_FIELD] = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
    return None


def _ensure_form_urlencoded_header(parsed: dict) -> None:
    headers = parsed.get("headers")
    if headers is None:
        parsed["headers"] = {"Content-Type": FORM_URLENCODED}
        return
    if not isinstance(headers, dict):
        return
    has_content_type = any(str(key).lower() == "content-type" for key in headers)
    if not has_content_type:
        parsed["headers"] = {**headers, "Content-Type": FORM_URLENCODED}


def _validate_int64_string(value: str, ticketer_idx: int, field: str) -> Optional[str]:
    invalid = (
        f"Ticketer at index {ticketer_idx}: 'config.{field}' must be a decimal int64 unix timestamp "
        "in the ticketer definition file"
    )
    try:
        parsed = int(value.strip(), 10)
    except (TypeError, ValueError):
        return invalid
    if parsed < INT64_MIN or parsed > INT64_MAX:
        return invalid
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
