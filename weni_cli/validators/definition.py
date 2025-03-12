from typing import Any
import rich_click as click
import regex
import yaml

from slugify import slugify

CONTACT_FIELD_NAME_REGEX = r"^[a-z][a-z0-9_]*$"


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

        # Validate description (required, must be string)
        if not agent_data.get("description"):
            return f"Agent '{agent_key}' is missing required field 'description' in the agent definition file"
        if not isinstance(agent_data["description"], str):
            return f"Agent '{agent_key}': 'description' must be a string in the agent definition file"

        # Instructions are optional, but if present must be a list of strings
        if "instructions" in agent_data:
            if not isinstance(agent_data["instructions"], list):
                return f"Agent '{agent_key}': 'instructions' must be an array in the agent definition file"
            for idx, instruction in enumerate(agent_data["instructions"]):
                if not isinstance(instruction, str):
                    return f"Agent '{agent_key}': instruction at index {idx} must be a string in the agent definition file"

        # Guardrails are optional, but if present must be a list of strings
        if "guardrails" in agent_data:
            if not isinstance(agent_data["guardrails"], list):
                return f"Agent '{agent_key}': 'guardrails' must be an array in the agent definition file"
            for idx, guardrail in enumerate(agent_data["guardrails"]):
                if not isinstance(guardrail, str):
                    return (
                        f"Agent '{agent_key}': guardrail at index {idx} must be a string in the agent definition file"
                    )

        # Validate skills
        if not agent_data.get("skills"):
            return f"Agent '{agent_key}' is missing required field 'skills' in the agent definition file"

        if not isinstance(agent_data["skills"], list):
            return f"Agent '{agent_key}': 'skills' must be an array in the agent definition file"

        # Validate each skill
        for skill_idx, skill_obj in enumerate(agent_data["skills"]):
            if not isinstance(skill_obj, dict):
                return (
                    f"Agent '{agent_key}': skill at index {skill_idx} must be an object in the agent definition file"
                )

            # Each skill object should have one key that is the skill name
            if len(skill_obj) != 1:
                return f"Agent '{agent_key}': skill at index {skill_idx} must have exactly one key in the agent definition file"

            skill_name = list(skill_obj.keys())[0]
            skill_data = skill_obj[skill_name]

            if not isinstance(skill_data, dict):
                return f"Agent '{agent_key}': skill '{skill_name}' data must be an object in the agent definition file"

            # Check required skill fields
            # Validate name (required, must be string)
            if not skill_data.get("name"):
                return f"Agent '{agent_key}': skill '{skill_name}' is missing required field 'name' in the agent definition file"
            if not isinstance(skill_data["name"], str):
                return (
                    f"Agent '{agent_key}': skill '{skill_name}': 'name' must be a string in the agent definition file"
                )

            # Validate description (required, must be string)
            if not skill_data.get("description"):
                return f"Agent '{agent_key}': skill '{skill_name}' is missing required field 'description' in the agent definition file"
            if not isinstance(skill_data["description"], str):
                return f"Agent '{agent_key}': skill '{skill_name}': 'description' must be a string in the agent definition file"

            # Validate source
            if skill_data.get("source") is None:
                return f"Agent '{agent_key}': skill '{skill_name}' is missing required field 'source' in the agent definition file"

            if not isinstance(skill_data["source"], dict):
                return f"Agent '{agent_key}': skill '{skill_name}': 'source' must be an object in the agent definition file"

            # Validate source path (required, must be string)
            if not skill_data["source"].get("path"):
                return f"Agent '{agent_key}': skill '{skill_name}': 'source' is missing required field 'path' in the agent definition file"
            if not isinstance(skill_data["source"]["path"], str):
                return f"Agent '{agent_key}': skill '{skill_name}': 'source.path' must be a string in the agent definition file"

            # Validate source entrypoint (required, must be string)
            if not skill_data["source"].get("entrypoint"):
                return f"Agent '{agent_key}': skill '{skill_name}': 'source' is missing required field 'entrypoint' in the agent definition file"
            if not isinstance(skill_data["source"]["entrypoint"], str):
                return f"Agent '{agent_key}': skill '{skill_name}': 'source.entrypoint' must be a string in the agent definition file"

            # Validate source path_test if present (must be string)
            if "path_test" in skill_data["source"] and not isinstance(skill_data["source"]["path_test"], str):
                return f"Agent '{agent_key}': skill '{skill_name}': 'source.path_test' must be a string in the agent definition file"

            # Validate parameters if present
            if "parameters" in skill_data:
                if not isinstance(skill_data["parameters"], list):
                    return f"Agent '{agent_key}': skill '{skill_name}': 'parameters' must be an array in the agent definition file"

                # Validate each parameter
                for param_idx, param_obj in enumerate(skill_data["parameters"]):
                    if not isinstance(param_obj, dict):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter at index {param_idx} must be an object in the agent definition file"

                    # Each parameter object should have one key that is the parameter name
                    if len(param_obj) != 1:
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter at index {param_idx} must have exactly one key in the agent definition file"

                    param_name = list(param_obj.keys())[0]
                    param_data = param_obj[param_name]

                    if not isinstance(param_data, dict):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' data must be an object in the agent definition file"

                    # Check required parameter fields
                    # Validate description (required, must be string)
                    if not param_data.get("description"):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' is missing required field 'description' in the agent definition file"
                    if not isinstance(param_data["description"], str):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' description must be a string in the agent definition file"

                    # Validate type (required, must be string)
                    if not param_data.get("type"):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' is missing required field 'type' in the agent definition file"
                    if not isinstance(param_data["type"], str):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' type must be a string in the agent definition file"

                    # Check allowed types
                    if param_data["type"] not in ["string", "number", "integer", "boolean", "array"]:
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' type must be one of: string, number, integer, boolean, array in the agent definition file"

                    # Validate required if present (must be boolean)
                    if "required" in param_data and not isinstance(param_data["required"], bool):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' required field must be a boolean in the agent definition file"

                    # Validate contact_field if present (must be boolean)
                    if "contact_field" in param_data and not isinstance(param_data["contact_field"], bool):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' contact_field must be a boolean in the agent definition file"

                    # If contact_field is True, validate parameter name

                    if param_data.get("contact_field") and not is_valid_contact_field_name(param_name):
                        return f"Agent '{agent_key}': skill '{skill_name}': parameter '{param_name}' name must match the regex of a valid contact field: {CONTACT_FIELD_NAME_REGEX} in the agent definition file"

    return None


def load_yaml_file(path) -> tuple[Any, str | None]:
    try:
        with open(path, "r") as file:
            return yaml.safe_load(file), None
    except Exception as error:
        return None, error


def load_agent_definition(path) -> tuple[Any, str | None]:
    data, error = load_yaml_file(path)
    if error:
        return None, error

    # Validate the schema
    error = validate_agent_definition_schema(data)
    if error:
        return None, error

    return data, None


def load_test_definition(path) -> tuple[Any, str | None]:
    data, error = load_yaml_file(path)
    if error:
        return None, error

    return data, None


# Updates the skills in the definition to be an array of objects containing name, path and slug
def format_definition(definition):
    agents = definition.get("agents", {})

    for agent in agents:
        skills = agents[agent].get("skills", {})
        agent_skills = []
        for skill in skills:
            for skill_name, skill_data in skill.items():

                parameters, err = validate_parameters(skill_data.get("parameters"))

                if err:
                    click.echo(f"Error in skill {skill_name}: {err}")
                    return None

                skill_slug = slugify(skill_data.get("name"))
                agent_skills.append(
                    {
                        "key": skill_name,
                        "slug": skill_slug,
                        "name": skill_data.get("name"),
                        "source": skill_data.get("source"),
                        "description": skill_data.get("description"),
                        "parameters": parameters,
                    }
                )

        agents[agent]["skills"] = agent_skills
        agents[agent]["slug"] = slugify(agents[agent].get("name"))

    return definition


def validate_parameters(parameters: dict) -> tuple[any, str]:
    if not parameters:
        return None, None

    def error(name, message):
        return f"parameter {name}: {message}"

    for parameter in parameters:
        for parameter_name, parameter_data in parameter.items():
            if not isinstance(parameter_data, dict):
                return None, error(parameter_name, "must be an object")

            description = parameter_data.get("description")
            parameter_type = parameter_data.get("type")
            required = parameter_data.get("required", None)
            contact_field = parameter_data.get("contact_field", None)

            if not description:
                return None, error(parameter_name, "description is required")

            if not isinstance(description, str):
                return None, error(parameter_name, "description must be a string")

            if not parameter_type:
                return None, error(parameter_name, "type is required")

            if parameter_type not in ["string", "number", "integer", "boolean", "array"]:
                return (
                    None,
                    error(parameter_name, "type must be one of: string, number, integer, boolean, array"),
                )

            if required is not None and not isinstance(required, bool):
                return None, error(parameter_name, "'required' field must be a boolean")

            if contact_field is not None and not isinstance(contact_field, bool):
                return None, error(parameter_name, "contact_field must be a boolean")

            if contact_field and not is_valid_contact_field_name(parameter_name):
                return (
                    None,
                    error(
                        parameter_name,
                        f"parameter name must match the regex of a valid contact field: {CONTACT_FIELD_NAME_REGEX}",
                    ),
                )

    return parameters, None


def is_valid_contact_field_name(parameter_name):
    if not regex.match(CONTACT_FIELD_NAME_REGEX, parameter_name, regex.V0):
        return False
    return True
