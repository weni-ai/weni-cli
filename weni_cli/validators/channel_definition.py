import re
from typing import Any, Optional
import yaml

# Constants for channel validation
MAX_CHANNEL_NAME_LENGTH = 100
AVAILABLE_CHANNEL_TYPES = ["E2"]  # External v2
AVAILABLE_SCHEMES = ["external"]
AVAILABLE_SEND_METHODS = ["POST", "GET", "PUT", "PATCH"]
AVAILABLE_CONTENT_TYPES = [
    "application/json",
    "application/x-www-form-urlencoded",
    "multipart/form-data",
]


def validate_channel_definition_schema(data):
    """
    Validates that the channel definition YAML contains all required fields and has a valid structure.

    Args:
        data (dict): Parsed YAML data

    Returns:
        str | None: Error message if validation fails, None otherwise
    """
    # Check that channels section exists
    if data.get("channels") is None:
        return "Missing required root key 'channels' in the channel definition file"

    if not isinstance(data["channels"], list):
        return "'channels' must be an array in the channel definition file"

    if not data["channels"]:
        return "No channels defined in the channel definition file"

    # Validate each channel
    for channel_idx, channel_data in enumerate(data["channels"]):
        if not isinstance(channel_data, dict):
            return f"Channel at index {channel_idx} must be an object in the channel definition file"

        # Validate name (required, must be string)
        if not channel_data.get("name"):
            return f"Channel at index {channel_idx} is missing required field 'name' in the channel definition file"
        if not isinstance(channel_data["name"], str):
            return f"Channel at index {channel_idx}: 'name' must be a string in the channel definition file"
        if len(channel_data["name"]) > MAX_CHANNEL_NAME_LENGTH:
            return f"Channel at index {channel_idx}: 'name' must be less than {MAX_CHANNEL_NAME_LENGTH} characters in the channel definition file"

        # Validate channel_type (required, must be string and valid type)
        if not channel_data.get("channel_type"):
            return f"Channel at index {channel_idx} is missing required field 'channel_type' in the channel definition file"
        if not isinstance(channel_data["channel_type"], str):
            return f"Channel at index {channel_idx}: 'channel_type' must be a string in the channel definition file"
        if channel_data["channel_type"] not in AVAILABLE_CHANNEL_TYPES:
            return f"Channel at index {channel_idx}: 'channel_type' must be one of: {', '.join(AVAILABLE_CHANNEL_TYPES)} in the channel definition file"

        # Validate schemes (required, must be array of strings)
        if "schemes" not in channel_data:
            return f"Channel at index {channel_idx} is missing required field 'schemes' in the channel definition file"
        if not isinstance(channel_data["schemes"], list):
            return f"Channel at index {channel_idx}: 'schemes' must be an array in the channel definition file"
        if not channel_data["schemes"]:
            return f"Channel at index {channel_idx}: 'schemes' must not be empty in the channel definition file"

        for scheme_idx, scheme in enumerate(channel_data["schemes"]):
            if not isinstance(scheme, str):
                return f"Channel at index {channel_idx}: scheme at index {scheme_idx} must be a string in the channel definition file"
            if scheme not in AVAILABLE_SCHEMES:
                return f"Channel at index {channel_idx}: scheme at index {scheme_idx} must be one of: {', '.join(AVAILABLE_SCHEMES)} in the channel definition file"

        # Validate config (required, must be object)
        if not channel_data.get("config"):
            return f"Channel at index {channel_idx} is missing required field 'config' in the channel definition file"
        if not isinstance(channel_data["config"], dict):
            return f"Channel at index {channel_idx}: 'config' must be an object in the channel definition file"

        config = channel_data["config"]

        # Validate required config fields
        required_config_fields = [
            "mo_response_content_type",
            "send_url",
            "send_method",
            "send_template",
            "content_type",
            "receive_template",
        ]

        for field in required_config_fields:
            if field not in config:
                return f"Channel at index {channel_idx}: 'config' is missing required field '{field}' in the channel definition file"

        # Validate mo_response_content_type (required, must be string and valid content type)
        if not isinstance(config["mo_response_content_type"], str):
            return f"Channel at index {channel_idx}: 'config.mo_response_content_type' must be a string in the channel definition file"
        if config["mo_response_content_type"] not in AVAILABLE_CONTENT_TYPES:
            return f"Channel at index {channel_idx}: 'config.mo_response_content_type' must be one of: {', '.join(AVAILABLE_CONTENT_TYPES)} in the channel definition file"

        # Validate mo_response (can be empty string)
        if "mo_response" in config and not isinstance(config["mo_response"], str):
            return f"Channel at index {channel_idx}: 'config.mo_response' must be a string in the channel definition file"

        # Validate mt_response_check (can be empty string)
        if "mt_response_check" in config and not isinstance(config["mt_response_check"], str):
            return f"Channel at index {channel_idx}: 'config.mt_response_check' must be a string in the channel definition file"

        # Validate send_url (required, must be string and valid URL)
        if not isinstance(config["send_url"], str):
            return f"Channel at index {channel_idx}: 'config.send_url' must be a string in the channel definition file"
        if not config["send_url"]:
            return f"Channel at index {channel_idx}: 'config.send_url' must not be empty in the channel definition file"
        # Basic URL validation
        url_pattern = re.compile(r"^https?://")
        if not url_pattern.match(config["send_url"]):
            return f"Channel at index {channel_idx}: 'config.send_url' must be a valid URL starting with http:// or https:// in the channel definition file"

        # Validate send_method (required, must be string and valid HTTP method)
        if not isinstance(config["send_method"], str):
            return f"Channel at index {channel_idx}: 'config.send_method' must be a string in the channel definition file"
        if config["send_method"] not in AVAILABLE_SEND_METHODS:
            return f"Channel at index {channel_idx}: 'config.send_method' must be one of: {', '.join(AVAILABLE_SEND_METHODS)} in the channel definition file"

        # Validate send_template (required, must be string)
        if not isinstance(config["send_template"], str):
            return f"Channel at index {channel_idx}: 'config.send_template' must be a string in the channel definition file"
        if not config["send_template"]:
            return f"Channel at index {channel_idx}: 'config.send_template' must not be empty in the channel definition file"

        # Validate content_type (required, must be string and valid content type)
        if not isinstance(config["content_type"], str):
            return f"Channel at index {channel_idx}: 'config.content_type' must be a string in the channel definition file"
        if config["content_type"] not in AVAILABLE_CONTENT_TYPES:
            return f"Channel at index {channel_idx}: 'config.content_type' must be one of: {', '.join(AVAILABLE_CONTENT_TYPES)} in the channel definition file"

        # Validate receive_template (required, must be string)
        if not isinstance(config["receive_template"], str):
            return f"Channel at index {channel_idx}: 'config.receive_template' must be a string in the channel definition file"
        if not config["receive_template"]:
            return f"Channel at index {channel_idx}: 'config.receive_template' must not be empty in the channel definition file"

        # Validate send_authorization (can be empty string)
        if "send_authorization" in config and not isinstance(config["send_authorization"], str):
            return f"Channel at index {channel_idx}: 'config.send_authorization' must be a string in the channel definition file"

    return None


def load_yaml_file(path) -> tuple[Any, Optional[Exception]]:
    """
    Loads and parses a YAML file.

    Args:
        path (str): Path to the YAML file

    Returns:
        tuple: (parsed_data, error) where error is None if successful
    """
    try:
        with open(path, "r") as file:
            return yaml.safe_load(file), None
    except Exception as error:
        return None, error


def load_channel_definition(path) -> tuple[Any, Optional[Exception]]:
    """
    Loads a channel definition from a YAML file.

    Args:
        path (str): Path to the channel definition file

    Returns:
        tuple: (parsed_data, error) where error is None if successful
    """
    data, error = load_yaml_file(path)
    if error:
        return None, error

    if not data:
        return None, Exception("Empty definition file")

    return data, None
