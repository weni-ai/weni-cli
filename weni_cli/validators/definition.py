import re
from typing import Any, Optional
import regex
import yaml

from slugify import slugify

MIN_INSTRUCTION_LENGTH = 40
MIN_GUARDRAIL_LENGTH = 40
MAX_AGENT_NAME_LENGTH = 55
MAX_TOOL_NAME_LENGTH = 40
AVAILABLE_COMPONENTS = [
    "cta_message",
    "quick_replies",
    "list_message",
    "catalog",
    "simple_text",
]


def validate_agent_definition_schema(data):
    """
    Validates that the agent definition YAML contains all required fields and has a valid structure.

    Args:
        data (dict): Parsed YAML data

    Returns:
        tuple: str | None indicating (error_message)
    """
    # Check that agents section exists
    if data.get("agents") is None:
        return "Missing required root key 'agents' in the agent definition file"

    if not isinstance(data["agents"], dict):
        return "'agents' must be an object in the agent definition file"

    if not data["agents"]:
        return "No agents defined in the agent definition file"

    # For each agent, validate required fields
    for agent_key, agent_data in data["agents"].items():
        # Check required agent fields
        if not isinstance(agent_data, dict):
            return f"Agent '{agent_key}' must be an object in the agent definition file"

        # Validate name (required, must be string)
        if not agent_data.get("name"):
            return f"Agent '{agent_key}' is missing required field 'name' in the agent definition file"
        if not isinstance(agent_data["name"], str):
            return f"Agent '{agent_key}': 'name' must be a string in the agent definition file"
        if len(agent_data["name"]) > MAX_AGENT_NAME_LENGTH:
            return f"Agent '{agent_key}': 'name' must be less than {MAX_AGENT_NAME_LENGTH} characters in the agent definition file"

        # Validate description (required, must be string)
        if not agent_data.get("description"):
            return f"Agent '{agent_key}' is missing required field 'description' in the agent definition file"
        if not isinstance(agent_data["description"], str):
            return f"Agent '{agent_key}': 'description' must be a string in the agent definition file"

        # Instructions are optional, but if present must be a list of strings, and each item must have a minimum of 40 characters
        if "instructions" in agent_data:
            if not isinstance(agent_data["instructions"], list):
                return f"Agent '{agent_key}': 'instructions' must be an array in the agent definition file"
            for idx, instruction in enumerate(agent_data["instructions"]):
                if not isinstance(instruction, str):
                    return f"Agent '{agent_key}': instruction at index {idx} must be a string in the agent definition file"
                if len(instruction) < MIN_INSTRUCTION_LENGTH:
                    return f"Agent '{agent_key}': instruction at index {idx} must have at least {MIN_INSTRUCTION_LENGTH} characters in the agent definition file"

        # Guardrails are optional, but if present must be a list of strings, and each item must have a minimum of 40 characters
        if "guardrails" in agent_data:
            if not isinstance(agent_data["guardrails"], list):
                return f"Agent '{agent_key}': 'guardrails' must be an array in the agent definition file"
            for idx, guardrail in enumerate(agent_data["guardrails"]):
                if not isinstance(guardrail, str):
                    return (
                        f"Agent '{agent_key}': guardrail at index {idx} must be a string in the agent definition file"
                    )
                if len(guardrail) < MIN_GUARDRAIL_LENGTH:
                    return f"Agent '{agent_key}': guardrail at index {idx} must have at least {MIN_GUARDRAIL_LENGTH} characters in the agent definition file"

        # Validate credentials if present (must be an object)
        if "credentials" in agent_data:
            if error := validate_agent_credentials(agent_key, agent_data["credentials"]):
                return error

        # Validate components, they are optional, but if present must be an array of objects
        if "components" in agent_data:
            if not isinstance(agent_data["components"], list):
                return f"Agent '{agent_key}': 'components' must be an array in the agent definition file"

            for idx, component in enumerate(agent_data["components"]):
                if not isinstance(component, dict):
                    return (
                        f"Agent '{agent_key}': component at index {idx} must be an object in the agent definition file"
                    )

                # Validate type (required, must be string)
                if "type" not in component:
                    return f"Agent '{agent_key}': component at index {idx} must have a 'type' field in the agent definition file"

                if component["type"] not in AVAILABLE_COMPONENTS:
                    return f"Agent '{agent_key}': component at index {idx} must have a 'type' field with one of the following values: {', '.join(AVAILABLE_COMPONENTS)} in the agent definition file"  # noqa: F821

                # Validate instructions if present (must be string)
                if "instructions" in component:
                    if not isinstance(component["instructions"], str):
                        return f"Agent '{agent_key}': component at index {idx} must have a 'instructions' field with a string value in the agent definition file"

        # Validate tools
        if not agent_data.get("tools"):
            return f"Agent '{agent_key}' is missing required field 'tools' in the agent definition file"

        if not isinstance(agent_data["tools"], list):
            return f"Agent '{agent_key}': 'tools' must be an array in the agent definition file"

        # Validate each tool
        for tool_idx, tool_obj in enumerate(agent_data["tools"]):
            if not isinstance(tool_obj, dict):
                return f"Agent '{agent_key}': tool at index {tool_idx} must be an object in the agent definition file"

            # Each tool object should have one key that is the tool name
            if len(tool_obj) != 1:
                return f"Agent '{agent_key}': tool at index {tool_idx} must have exactly one key in the agent definition file"

            tool_name = list(tool_obj.keys())[0]
            tool_data = tool_obj[tool_name]

            if not isinstance(tool_data, dict):
                return f"Agent '{agent_key}': tool '{tool_name}' data must be an object in the agent definition file"

            # Check required tool fields
            # Validate name (required, must be string)
            if not tool_data.get("name"):
                return f"Agent '{agent_key}': tool '{tool_name}' is missing required field 'name' in the agent definition file"
            if not isinstance(tool_data["name"], str):
                return f"Agent '{agent_key}': tool '{tool_name}': 'name' must be a string in the agent definition file"
            if len(tool_data["name"]) > MAX_TOOL_NAME_LENGTH:
                return f"Agent '{agent_key}': tool '{tool_name}': 'name' must be less than {MAX_TOOL_NAME_LENGTH} characters in the agent definition file"

            # Validate description (required, must be string)
            if not tool_data.get("description"):
                return f"Agent '{agent_key}': tool '{tool_name}' is missing required field 'description' in the agent definition file"
            if not isinstance(tool_data["description"], str):
                return f"Agent '{agent_key}': tool '{tool_name}': 'description' must be a string in the agent definition file"

            # Validate source
            if tool_data.get("source") is None:
                return f"Agent '{agent_key}': tool '{tool_name}' is missing required field 'source' in the agent definition file"

            if not isinstance(tool_data["source"], dict):
                return (
                    f"Agent '{agent_key}': tool '{tool_name}': 'source' must be an object in the agent definition file"
                )

            # Validate source path (required, must be string)
            if not tool_data["source"].get("path"):
                return f"Agent '{agent_key}': tool '{tool_name}': 'source' is missing required field 'path' in the agent definition file"
            if not isinstance(tool_data["source"]["path"], str):
                return f"Agent '{agent_key}': tool '{tool_name}': 'source.path' must be a string in the agent definition file"

            # Validate source entrypoint (required, must be string)
            if not tool_data["source"].get("entrypoint"):
                return f"Agent '{agent_key}': tool '{tool_name}': 'source' is missing required field 'entrypoint' in the agent definition file"
            if not isinstance(tool_data["source"]["entrypoint"], str):
                return f"Agent '{agent_key}': tool '{tool_name}': 'source.entrypoint' must be a string in the agent definition file"

            # Validate source path_test if present (must be string)
            if "path_test" in tool_data["source"] and not isinstance(tool_data["source"]["path_test"], str):
                return f"Agent '{agent_key}': tool '{tool_name}': 'source.path_test' must be a string in the agent definition file"

            # Validate parameters if present
            if "parameters" in tool_data:
                if not isinstance(tool_data["parameters"], list):
                    return f"Agent '{agent_key}': tool '{tool_name}': 'parameters' must be an array in the agent definition file"

                # Validate each parameter
                for param_idx, param_obj in enumerate(tool_data["parameters"]):
                    if not isinstance(param_obj, dict):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter at index {param_idx} must be an object in the agent definition file"

                    # Each parameter object should have one key that is the parameter name
                    if len(param_obj) != 1:
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter at index {param_idx} must have exactly one key in the agent definition file"

                    param_name = list(param_obj.keys())[0]
                    param_data = param_obj[param_name]

                    if not isinstance(param_data, dict):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' data must be an object in the agent definition file"

                    # Check required parameter fields
                    # Validate description (required, must be string)
                    if not param_data.get("description"):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' is missing required field 'description' in the agent definition file"
                    if not isinstance(param_data["description"], str):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' description must be a string in the agent definition file"

                    # Validate type (required, must be string)
                    if not param_data.get("type"):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' is missing required field 'type' in the agent definition file"
                    if not isinstance(param_data["type"], str):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' type must be a string in the agent definition file"

                    # Check allowed types
                    if param_data["type"] not in [
                        "string",
                        "number",
                        "integer",
                        "boolean",
                        "array",
                    ]:
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' type must be one of: string, number, integer, boolean, array in the agent definition file"

                    # Validate required if present (must be boolean)
                    if "required" in param_data and not isinstance(param_data["required"], bool):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' required field must be a boolean in the agent definition file"

                    # Validate contact_field if present (must be boolean)
                    if "contact_field" in param_data and not isinstance(param_data["contact_field"], bool):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' contact_field must be a boolean in the agent definition file"

                    # If contact_field is True, validate parameter name

                    if param_data.get("contact_field") and not ContactFieldValidator.has_valid_contact_field_name(
                        param_name
                    ):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' name must match the regex of a valid contact field: {re.escape(ContactFieldValidator.CONTACT_FIELD_NAME_REGEX)} in the agent definition file"

                    if param_data.get("contact_field") and not ContactFieldValidator.has_valid_contact_field_length(
                        param_name
                    ):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' name must be {ContactFieldValidator.CONTACT_FIELD_MAX_LENGTH} characters or less in the agent definition file"

                    if param_data.get("contact_field") and not ContactFieldValidator.has_allowed_parameter_name(
                        param_name
                    ):
                        return f"Agent '{agent_key}': tool '{tool_name}': parameter '{param_name}' name must not be a reserved contact field name in the agent definition file\nRestricted contact field names: {ContactFieldValidator.RESERVED_CONTACT_FIELDS}"


def validate_active_agent_definition_schema(data):
    # Check that agents section exists
    if data.get("agents") is None:
        return "Missing required root key 'agents' in the agent definition file"

    if not isinstance(data["agents"], dict):
        return "'agents' must be an object in the agent definition file"

    if not data["agents"]:
        return "No agents defined in the agent definition file"

    # For each agent, validate required fields
    for agent_key, agent_data in data["agents"].items():
        # Check required agent fields
        if not isinstance(agent_data, dict):
            return f"Agent '{agent_key}' must be an object in the agent definition file"

        # Validate name (required, must be string)
        if not agent_data.get("name"):
            return f"Agent '{agent_key}' is missing required field 'name' in the agent definition file"
        if not isinstance(agent_data["name"], str):
            return f"Agent '{agent_key}': 'name' must be a string in the agent definition file"
        if len(agent_data["name"]) > MAX_AGENT_NAME_LENGTH:
            return f"Agent '{agent_key}': 'name' must be less than {MAX_AGENT_NAME_LENGTH} characters in the agent definition file"

        # Validate description (required, must be string)
        if not agent_data.get("description"):
            return f"Agent '{agent_key}' is missing required field 'description' in the agent definition file"
        if not isinstance(agent_data["description"], str):
            return f"Agent '{agent_key}': 'description' must be a string in the agent definition file"

        # Validate language (required, must be a string and valid language code)
        if not agent_data.get("language"):
            return f"Agent '{agent_key}' is missing required field 'language' in the agent definition file"
        if not isinstance(agent_data["language"], str):
            return f"Agent '{agent_key}': 'language' must be a string in the agent definition file"
        if not LanguageValidator.is_valid_language(agent_data["language"]):
            return f"Agent '{agent_key}': 'language' must be one of the following values: {', '.join(LanguageValidator.AVAILABLE_LANGUAGES)} in the agent definition file"

        # Validate credentials if present (must be an object)
        if "credentials" in agent_data:
            if error := validate_agent_credentials(agent_key, agent_data["credentials"]):
                return error

        # Validate rules if present (must be a dictionary)
        if "rules" in agent_data:
            if not isinstance(agent_data["rules"], dict):
                return f"Agent '{agent_key}': 'rules' must be an object in the agent definition file"

            # Validate each rule
            for rule_key, rule_data in agent_data["rules"].items():
                # Validate rule data is a dictionary
                if not isinstance(rule_data, dict):
                    return (
                        f"Agent '{agent_key}': rule '{rule_key}' data must be an object in the agent definition file"
                    )

                # Validate template (required, must be string)
                if not rule_data.get("template"):
                    return f"Agent '{agent_key}': rule '{rule_key}' is missing required field 'template' in the agent definition file"
                if not isinstance(rule_data["template"], str):
                    return f"Agent '{agent_key}': rule '{rule_key}': 'template' must be a string in the agent definition file"

                # Validate template has no whitespace
                if " " in rule_data["template"]:
                    return f"Agent '{agent_key}': rule '{rule_key}': 'template' must not contain whitespace. Use underscores instead in the agent definition file"

                # Validate source
                if rule_data.get("source") is None:
                    return f"Agent '{agent_key}': rule '{rule_key}' is missing required field 'source' in the agent definition file"

                if not isinstance(rule_data["source"], dict):
                    return f"Agent '{agent_key}': rule '{rule_key}': 'source' must be an object in the agent definition file"

                # Validate source path (required, must be string)
                if not rule_data["source"].get("path"):
                    return f"Agent '{agent_key}': rule '{rule_key}': 'source' is missing required field 'path' in the agent definition file"
                if not isinstance(rule_data["source"]["path"], str):
                    return f"Agent '{agent_key}': rule '{rule_key}': 'source.path' must be a string in the agent definition file"

                # Validate source entrypoint (required, must be string)
                if not rule_data["source"].get("entrypoint"):
                    return f"Agent '{agent_key}': rule '{rule_key}': 'source' is missing required field 'entrypoint' in the agent definition file"
                if not isinstance(rule_data["source"]["entrypoint"], str):
                    return f"Agent '{agent_key}': rule '{rule_key}': 'source.entrypoint' must be a string in the agent definition file"

                # Validate start_condition (required, must be a string)
                if not rule_data.get("start_condition"):
                    return f"Agent '{agent_key}': rule '{rule_key}' is missing required field 'start_condition' in the agent definition file"
                if not isinstance(rule_data["start_condition"], str):
                    return f"Agent '{agent_key}': rule '{rule_key}': 'start_condition' must be a string in the agent definition file"

                # Validate display_name (required, must be a string)
                if not rule_data.get("display_name"):
                    return f"Agent '{agent_key}': rule '{rule_key}' is missing required field 'display_name' in the agent definition file"
                if not isinstance(rule_data["display_name"], str):
                    return f"Agent '{agent_key}': rule '{rule_key}': 'display_name' must be a string in the agent definition file"

        # Validate pre-processing (required, must be a dictionary)
        if "pre-processing" in agent_data:
            if not isinstance(agent_data["pre-processing"], dict):
                return f"Agent '{agent_key}': 'pre-processing' must be an object in the agent definition file"

            # Validate source
            if agent_data["pre-processing"].get("source") is None:
                return f"Agent '{agent_key}': 'pre-processing' is missing required field 'source' in the agent definition file"

            if not isinstance(agent_data["pre-processing"]["source"], dict):
                return f"Agent '{agent_key}': 'pre-processing.source' must be an object in the agent definition file"

            # Validate source path (required, must be string)
            if not agent_data["pre-processing"]["source"].get("path"):
                return f"Agent '{agent_key}': 'pre-processing.source' is missing required field 'path' in the agent definition file"
            if not isinstance(agent_data["pre-processing"]["source"]["path"], str):
                return (
                    f"Agent '{agent_key}': 'pre-processing.source.path' must be a string in the agent definition file"
                )

            # Validate source entrypoint (required, must be string)
            if not agent_data["pre-processing"]["source"].get("entrypoint"):
                return f"Agent '{agent_key}': 'pre-processing.source' is missing required field 'entrypoint' in the agent definition file"
            if not isinstance(agent_data["pre-processing"]["source"]["entrypoint"], str):
                return f"Agent '{agent_key}': 'pre-processing.source.entrypoint' must be a string in the agent definition file"

            # Validate result_examples_file (required, must be a string with a .json in suffix)
            if "result_examples_file" not in agent_data["pre-processing"]:
                return f"Agent '{agent_key}': 'pre-processing' is missing required field 'result_examples_file' in the agent definition file"

            result_examples_file = agent_data["pre-processing"]["result_examples_file"]
            if not isinstance(result_examples_file, str) or not result_examples_file.endswith(".json"):
                return f"Agent '{agent_key}': 'pre-processing.result_examples_file' must be a string with a .json in suffix in the agent definition file"

    return None


def validate_agent_credentials(agent_key: str, credentials: Any) -> Optional[str]:
    # Validate credentials if present (must be an object)
    if not isinstance(credentials, dict):
        return f"Agent '{agent_key}': 'credentials' must be an object in the agent definition file"

    # Validate each credential (must be an object)
    for credential_key, credential_value in credentials.items():
        if not isinstance(credential_value, dict):
            return f"Agent '{agent_key}': value for credential '{credential_key}' must be an object in the agent definition file"

        # Validate label (required, must be a string)
        if not credential_value.get("label"):
            return f"Agent '{agent_key}': 'label' for credential '{credential_key}' is missing in the agent definition file"
        if not isinstance(credential_value["label"], str):
            return f"Agent '{agent_key}': 'label' for credential '{credential_key}' must be a string in the agent definition file"

        # Validate placeholder (required, must be a string)
        if not credential_value.get("placeholder"):
            return f"Agent '{agent_key}': 'placeholder' for credential '{credential_key}' is missing in the agent definition file"
        if not isinstance(credential_value["placeholder"], str):
            return f"Agent '{agent_key}': 'placeholder' for credential '{credential_key}' must be a string in the agent definition file"

        # Validate is_confidential if present (must be a boolean)
        if "is_confidential" in credential_value and not isinstance(credential_value["is_confidential"], bool):
            return f"Agent '{agent_key}': 'is_confidential' for credential '{credential_key}' must be a boolean in the agent definition file"

    return None


def load_yaml_file(path) -> tuple[Any, Optional[Exception]]:
    try:
        with open(path, "r") as file:
            return yaml.safe_load(file), None
    except Exception as error:
        return None, error


def load_agent_definition(path) -> tuple[Any, Optional[Exception]]:
    data, error = load_yaml_file(path)
    if error:
        return None, error

    if not data:
        return None, Exception("Empty definition file")

    return data, None


def load_test_definition(path) -> tuple[Any, Optional[Exception]]:
    data, error = load_yaml_file(path)
    if error:
        return None, error

    return data, None


# Updates the tools in the definition to be an array of objects containing name, path and slug
def format_definition(definition: dict) -> Optional[dict]:
    agents = definition.get("agents", {})

    for agent in agents:
        tools = agents[agent].get("tools", {})
        agent_tools = []
        for tool in tools:
            for tool_key, tool_data in tool.items():
                tool_slug = slugify(tool_data.get("name"))
                agent_tools.append(
                    {
                        "key": tool_key,
                        "slug": tool_slug,
                        "name": tool_data.get("name"),
                        "source": tool_data.get("source"),
                        "description": tool_data.get("description"),
                        "parameters": tool_data.get("parameters"),
                    }
                )

        agents[agent]["tools"] = agent_tools
        agents[agent]["slug"] = slugify(agents[agent].get("name"))

    return definition


class ContactFieldValidator:
    CONTACT_FIELD_NAME_REGEX = r"^[a-z][a-z0-9_]*$"
    CONTACT_FIELD_MAX_LENGTH = 36
    RESERVED_CONTACT_FIELDS = [
        "id",
        "name",
        "first_name",
        "language",
        "groups",
        "uuid",
        "created_on",
        "created_by",
        "modified_by",
        "is",
        "has",
        "mailto",
        "ext",
        "facebook",
        "jiochat",
        "line",
        "tel",
        "telegram",
        "twilio",
        "twitter",
        "twitterid",
        "viber",
        "vk",
        "fcm",
        "whatsapp",
        "wechat",
        "freshchat",
        "rocketchat",
        "discord",
        "weniwebchat",
        "instagram",
        "slack",
        "teams",
    ]

    @staticmethod
    def has_valid_contact_field_name(parameter_name) -> bool:
        if not regex.match(ContactFieldValidator.CONTACT_FIELD_NAME_REGEX, parameter_name, regex.V0):
            return False
        return True

    @staticmethod
    def has_allowed_parameter_name(parameter_name) -> bool:
        if parameter_name in ContactFieldValidator.RESERVED_CONTACT_FIELDS:
            return False
        return True

    @staticmethod
    def has_valid_contact_field_length(parameter_name) -> bool:
        if len(parameter_name) > ContactFieldValidator.CONTACT_FIELD_MAX_LENGTH:
            return False
        return True


class LanguageValidator:
    AVAILABLE_LANGUAGES = [
        "af",
        "sq",
        "ar",
        "az",
        "bn",
        "bg",
        "ca",
        "zh_CN",
        "zh_HK",
        "zh_TW",
        "hr",
        "cs",
        "da",
        "nl",
        "en",
        "en_GB",
        "en_US",
        "et",
        "fil",
        "fi",
        "fr",
        "de",
        "el",
        "gu",
        "ha",
        "he",
        "hi",
        "hu",
        "id",
        "ga",
        "it",
        "ja",
        "kn",
        "kk",
        "ko",
        "ky_KG",
        "lo",
        "lv",
        "lt",
        "ml",
        "mk",
        "ms",
        "mr",
        "nb",
        "fa",
        "pl",
        "pt_BR",
        "pt_PT",
        "pa",
        "ro",
        "ru",
        "sr",
        "sk",
        "sl",
        "es",
        "es_AR",
        "es_ES",
        "es_MX",
        "sw",
        "sv",
        "ta",
        "te",
        "th",
        "tr",
        "uk",
        "ur",
        "uz",
        "vi",
        "zu",
    ]

    @staticmethod
    def is_valid_language(language_code: str) -> bool:
        return language_code in LanguageValidator.AVAILABLE_LANGUAGES
