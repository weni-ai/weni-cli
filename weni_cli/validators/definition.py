import rich_click as click
import regex
import yaml

from slugify import slugify

CONTACT_FIELD_NAME_REGEX = r"^[a-z][a-z0-9_]*$"


def load_definition(path):
    with open(path, "r") as file:
        try:
            data = yaml.safe_load(file)
        except Exception as error:
            click.echo(f"Failed to parse definition file: {error}")
            return None

        if not data:
            click.echo("Error: Empty definition file")
            return None

        return data


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

            if not parameter_data.get("description"):
                return None, error(parameter_name, "description is required")

            if type(parameter_data.get("description")) != str:
                return None, error(parameter_name, "description must be a string")

            if not parameter_data.get("type"):
                return None, error(parameter_name, "type is required")

            if parameter_data.get("type") not in ["string", "number", "integer", "boolean", "array"]:
                return (
                    None,
                    error(parameter_name, "type must be one of: string, number, integer, boolean, array"),
                )

            if type(parameter_data.get("required", None)) != bool:
                return None, error(parameter_name, "'required' field must be a boolean")

            if parameter_data.get("contact_field", None) and type(parameter_data.get("contact_field")) != bool:
                return None, error(parameter_name, "contact_field must be a boolean")

            if parameter_data.get("contact_field", None) and not is_valid_contact_field_name(parameter_name):
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
