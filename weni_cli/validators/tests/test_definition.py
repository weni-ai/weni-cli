import pytest
import regex
from click.testing import CliRunner
from weni_cli.validators.definition import (
    load_yaml_file,
    load_agent_definition,
    format_definition,
    validate_parameters,
    is_valid_contact_field_name,
    CONTACT_FIELD_NAME_REGEX,
    validate_agent_definition_schema,
    load_test_definition,
)


@pytest.fixture
def sample_definition_file():
    """Create a sample definition file for testing."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a valid definition file
        with open("valid_definition.yaml", "w") as f:
            f.write(
                """
agents:
  test_agent:
    name: Test Agent
    description: Test Description
    skills:
      - test_skill:
          name: Test Skill
          description: A test skill
          source:
            path: skills/test_skill
            entrypoint: main.TestSkill
          parameters:
            - test_param:
                type: string
                description: Test parameter
                required: true
            - optional_param:
                type: number
                description: Optional parameter
            - contact_param:
                type: string
                description: Contact field parameter
                contact_field: true
            """
            )

        # Create an invalid definition file (syntax error)
        with open("invalid_definition.yaml", "w") as f:
            f.write(
                """
agents:
  test_agent
    name: Test Agent
    skills:
      - test_skill:
          name: Test Skill
            """
            )

        # Create an empty definition file
        with open("empty_definition.yaml", "w") as f:
            f.write("")

        yield {
            "valid_path": "valid_definition.yaml",
            "invalid_path": "invalid_definition.yaml",
            "empty_path": "empty_definition.yaml",
        }


@pytest.fixture
def valid_definition():
    """Return a valid definition dictionary."""
    return {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "skills": [
                    {
                        "test_skill": {
                            "name": "Test Skill",
                            "description": "A test skill",
                            "source": {"path": "skills/test_skill"},
                            "parameters": [
                                {"test_param": {"type": "string", "description": "Test parameter", "required": True}},
                                {"optional_param": {"type": "number", "description": "Optional parameter"}},
                            ],
                        }
                    }
                ],
            }
        }
    }


def test_load_yaml_file_valid(sample_definition_file):
    """Test loading a valid definition file."""
    data, error = load_yaml_file(sample_definition_file["valid_path"])

    # Check that there's no error
    assert error is None

    # Check that the result is a dictionary
    assert isinstance(data, dict)

    # Check that the expected data was loaded
    assert "agents" in data
    assert "test_agent" in data["agents"]
    assert data["agents"]["test_agent"]["name"] == "Test Agent"
    assert isinstance(data["agents"]["test_agent"]["skills"], list)


def test_load_yaml_file_invalid(sample_definition_file):
    """Test loading an invalid definition file."""
    data, error = load_yaml_file(sample_definition_file["invalid_path"])

    # Check that the data is None
    assert data is None

    # Check that we got an error
    assert error is not None
    assert "mapping values are not allowed here" in str(error)


def test_load_yaml_file_empty(sample_definition_file):
    """Test loading an empty definition file."""
    data, error = load_yaml_file(sample_definition_file["empty_path"])

    # For an empty file, YAML returns None but no error
    assert data is None
    assert error is None


def test_load_yaml_file_nonexistent():
    """Test loading a non-existent definition file."""
    # The load_yaml_file function should catch FileNotFoundError
    data, error = load_yaml_file("nonexistent_file.yaml")

    # Check that we have an error
    assert data is None
    assert error is not None
    assert isinstance(error, FileNotFoundError)


def test_format_definition_valid(valid_definition):
    """Test formatting a valid definition."""
    result = format_definition(valid_definition)

    # Check that the result is a dictionary
    assert isinstance(result, dict)

    # Check that agents are present
    assert "agents" in result
    assert "test_agent" in result["agents"]

    # Check that the slug was added
    assert result["agents"]["test_agent"]["slug"] == "test-agent"

    # Check that skills were reformatted
    skills = result["agents"]["test_agent"]["skills"]
    assert isinstance(skills, list)
    assert "key" in skills[0]
    assert "slug" in skills[0]
    assert "name" in skills[0]
    assert skills[0]["key"] == "test_skill"
    assert skills[0]["slug"] == "test-skill"
    assert skills[0]["name"] == "Test Skill"


def test_format_definition_invalid_parameter(mocker):
    """Test formatting a definition with invalid parameters."""
    # Mock rich_click.echo to capture messages
    mock_echo = mocker.patch("rich_click.echo")

    # Create a definition with an invalid parameter (missing type)
    definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "skills": [
                    {
                        "test_skill": {
                            "name": "Test Skill",
                            "parameters": [
                                {
                                    "invalid_param": {
                                        "description": "Invalid parameter"
                                        # Missing type field
                                    }
                                }
                            ],
                        }
                    }
                ],
            }
        }
    }

    result = format_definition(definition)

    # Check that the result is None
    assert result is None

    # Check that an error message was displayed
    mock_echo.assert_called_once()
    assert "Error in skill test_skill" in mock_echo.call_args[0][0]
    assert "type is required" in mock_echo.call_args[0][0]


def test_format_definition_no_skills():
    """Test formatting a definition with no skills."""
    definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent"
                # No skills
            }
        }
    }

    result = format_definition(definition)

    # Check that the result is a dictionary
    assert isinstance(result, dict)

    # Check that agents are present
    assert "agents" in result
    assert "test_agent" in result["agents"]

    # Check that the slug was added
    assert result["agents"]["test_agent"]["slug"] == "test-agent"

    # Check that skills is an empty list
    skills = result["agents"]["test_agent"]["skills"]
    assert isinstance(skills, list)
    assert len(skills) == 0


def test_validate_parameters_valid():
    """Test validating valid parameters."""
    # Create valid parameters
    parameters = [
        {"test_param": {"type": "string", "description": "Test parameter", "required": True}},
        {"number_param": {"type": "number", "description": "Number parameter"}},
        {"array_param": {"type": "array", "description": "Array parameter", "required": False}},
        {"contact_field_param": {"type": "string", "description": "Contact field parameter", "contact_field": True}},
    ]

    result, error = validate_parameters(parameters)

    # Check that there's no error
    assert error is None

    # Check that the result is the original parameters
    assert result == parameters


def test_validate_parameters_none():
    """Test validating None parameters."""
    result, error = validate_parameters(None)

    # Check that there's no error
    assert error is None

    # Check that the result is None
    assert result is None


def test_validate_parameters_invalid_parameter_type():
    """Test validating a parameter with an invalid type."""
    # Create parameters with an invalid type
    parameters = [{"test_param": {"type": "invalid_type", "description": "Test parameter"}}]

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error
    assert error is not None
    assert "parameter test_param: type must be one of:" in error


def test_validate_parameters_missing_description():
    """Test validating a parameter with a missing description."""
    # Create parameters with a missing description
    parameters = [
        {
            "test_param": {
                "type": "string"
                # Missing description
            }
        }
    ]

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error
    assert error is not None
    assert "parameter test_param: description is required" in error


def test_validate_parameters_missing_type():
    """Test validating a parameter with a missing type."""
    # Create parameters with a missing type
    parameters = [
        {
            "test_param": {
                "description": "Test parameter"
                # Missing type
            }
        }
    ]

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error
    assert error is not None
    assert "parameter test_param: type is required" in error


def test_validate_parameters_non_dict():
    """Test validating a parameter that's not a dictionary."""
    # Looking at the actual implementation, the function expects parameter_data to be a dict
    # with get() method. Let's create a more accurate test case where the issue occurs
    # after the initial string check.

    # Create parameters with non-dict nested inside a parameter that looks valid from outside
    parameters = [
        {
            "test_param": {
                "description": "Test parameter",
                "type": "string",
                "required": "not_a_boolean",  # This should trigger the boolean check
            }
        }
    ]

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error
    assert error is not None
    assert "parameter test_param: 'required' field must be a boolean" in error


def test_validate_parameters_invalid_required():
    """Test validating a parameter with an invalid required field."""
    # Create parameters with an invalid required field
    parameters = [{"test_param": {"type": "string", "description": "Test parameter", "required": "not_a_boolean"}}]

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error
    assert error is not None
    assert "parameter test_param: 'required' field must be a boolean" in error


def test_validate_parameters_invalid_contact_field():
    """Test validating a parameter with an invalid contact_field field."""
    # Create parameters with an invalid contact_field field
    parameters = [
        {"test_param": {"type": "string", "description": "Test parameter", "contact_field": "not_a_boolean"}}
    ]

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error
    assert error is not None
    assert "parameter test_param: contact_field must be a boolean" in error


def test_validate_parameters_invalid_contact_field_name():
    """Test validating a parameter with an invalid name for a contact field."""
    # Create parameters with an invalid name for a contact field
    parameters = [{"Invalid-Name": {"type": "string", "description": "Test parameter", "contact_field": True}}]

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error
    assert error is not None
    assert "parameter Invalid-Name: parameter name must match the regex of a valid contact field" in error


def test_is_valid_contact_field_name_valid():
    """Test valid contact field names."""
    valid_names = ["valid", "valid123", "valid_name", "a123_456"]

    for name in valid_names:
        assert is_valid_contact_field_name(name) is True


def test_is_valid_contact_field_name_invalid():
    """Test invalid contact field names."""
    invalid_names = ["123invalid", "Invalid", "invalid-name", "_invalid", "invalid.name"]

    for name in invalid_names:
        assert is_valid_contact_field_name(name) is False


def test_contact_field_regex_pattern():
    """Test the contact field regex pattern directly."""
    # This test ensures the regex pattern matches what we expect
    valid_names = ["valid", "valid123", "valid_name", "a123_456"]
    invalid_names = ["123invalid", "Invalid", "invalid-name", "_invalid", "invalid.name"]

    for name in valid_names:
        assert regex.match(CONTACT_FIELD_NAME_REGEX, name, regex.V0) is not None

    for name in invalid_names:
        assert regex.match(CONTACT_FIELD_NAME_REGEX, name, regex.V0) is None


def test_validate_parameters_description_not_string():
    """Test validating a parameter with a description that's not a string."""
    # Create parameters with a description that's not a string
    parameters = [{"test_param": {"type": "string", "description": 123, "required": True}}]  # Not a string

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error
    assert error is not None
    assert "parameter test_param: description must be a string" in error


def test_validate_parameters_non_dictionary():
    """Test validating a parameter where parameter_data is not a dictionary."""
    # Create parameters where parameter_data is not a dictionary, but a string
    parameters = [{"test_param": "not a dictionary"}]

    result, error = validate_parameters(parameters)

    # Check that the result is None
    assert result is None

    # Check that there's an error message
    assert error is not None
    assert "parameter test_param: must be an object" in error


def test_validate_agent_definition_calls_validate_schema(mocker, tmpdir):
    """Test that load_agent_definition calls validate_agent_definition_schema."""
    # Create a temporary YAML file
    yaml_file = tmpdir.join("test_definition.yaml")
    yaml_file.write(
        """
    agents:
      test_agent:
        name: Test Agent
        description: Test description
        instructions: [Instruction 1]
        skills: []
    """
    )

    # Mock validate_agent_definition_schema
    mock_validate = mocker.patch(
        "weni_cli.validators.definition.validate_agent_definition_schema", return_value=None  # No error means valid
    )

    # Call load_agent_definition
    result, error = load_agent_definition(str(yaml_file))

    # Verify validate_agent_definition_schema was called
    mock_validate.assert_called_once()

    # Verify load_agent_definition returns data when validation passes
    assert result is not None
    assert error is None
    assert "agents" in result


def test_load_agent_definition_fails_on_invalid_schema(mocker, tmpdir):
    """Test that load_agent_definition returns error when schema validation fails."""
    # Create a temporary YAML file
    yaml_file = tmpdir.join("invalid_definition.yaml")
    yaml_file.write(
        """
    agents:
      test_agent:
        # Missing required fields
    """
    )

    # Mock validate_agent_definition_schema
    error_message = "Test error message"
    mocker.patch("weni_cli.validators.definition.validate_agent_definition_schema", return_value=error_message)

    # Call load_agent_definition
    result, error = load_agent_definition(str(yaml_file))

    # Verify error message is returned
    assert result is None
    assert error == error_message


def test_validate_definition_without_agents():
    """Test that a definition without agents is invalid."""
    invalid_definition = {}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Missing required root key 'agents' in the agent definition file" in error


def test_validate_definition_with_invalid_agents_type():
    """Test that a definition with invalid agents type is invalid."""
    invalid_definition = {"agents": "Not a dictionary"}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "'agents' must be an object in the agent definition file" in error


def test_validate_definition_with_empty_agents():
    """Test that a definition with empty agents is invalid."""
    invalid_definition = {"agents": {}}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "No agents defined in the agent definition file" in error


def test_validate_definition_without_instructions():
    """Test that a definition without instructions is valid."""
    valid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                # No instructions key
                "skills": [
                    {
                        "test_skill": {
                            "name": "Test Skill",
                            "description": "Test skill description",
                            "source": {
                                "path": "skills/test",
                                "entrypoint": "main.TestSkill",
                            },
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(valid_definition)
    assert error is None


def test_validate_definition_without_guardrails():
    """Test that a definition without guardrails is valid."""
    valid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                # No guardrails key
                "skills": [
                    {
                        "test_skill": {
                            "name": "Test Skill",
                            "description": "Test skill description",
                            "source": {
                                "path": "skills/test",
                                "entrypoint": "main.TestSkill",
                            },
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(valid_definition)
    assert error is None


def test_validate_definition_with_invalid_instructions():
    """Test validation fails when instructions is not an array."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": "Not an array",  # String instead of array
                "skills": [
                    {
                        "test_skill": {
                            "name": "Test Skill",
                            "description": "Test skill description",
                            "source": {
                                "path": "skills/test",
                                "entrypoint": "main.TestSkill",
                            },
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "'instructions' must be an array" in error


def test_validate_definition_with_invalid_guardrails():
    """Test validation fails when guardrails is not an array."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": "Not an array",  # String instead of array
                "skills": [
                    {
                        "test_skill": {
                            "name": "Test Skill",
                            "description": "Test skill description",
                            "source": {
                                "path": "skills/test",
                                "entrypoint": "main.TestSkill",
                            },
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "'guardrails' must be an array" in error


def test_validate_definition_with_invalid_agent_data():
    """Test validation fails when agent data is invalid."""
    invalid_definition = {"agents": {"test_agent": "Not a dictionary"}}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent' must be an object in the agent definition file" in error


def test_validate_definition_with_missing_agent_name():
    """Test validation fails when agent name is missing."""
    invalid_definition = {"agents": {"test_agent": {}}}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent' is missing required field 'name' in the agent definition file" in error


def test_validate_definition_with_invalid_agent_name():
    """Test validation fails when agent name is invalid."""
    invalid_definition = {"agents": {"test_agent": {"name": 123}}}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'name' must be a string in the agent definition file" in error


def test_validate_definition_with_missing_agent_description():
    """Test validation fails when agent description is missing."""
    invalid_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent' is missing required field 'description' in the agent definition file" in error


def test_validate_definition_with_invalid_agent_description():
    """Test validation fails when agent description is invalid."""
    invalid_definition = {"agents": {"test_agent": {"name": "Test Agent", "description": 123}}}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'description' must be a string in the agent definition file" in error


def test_validate_definition_with_invalid_agent_instructions():
    """Test validation fails when agent instructions is not an array."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": "Not an array",  # String instead of array
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'instructions' must be an array in the agent definition file" in error


def test_validate_definition_with_invalid_agent_guardrails():
    """Test validation fails when agent guardrails is not an array."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": "Not an array",  # String instead of array
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'guardrails' must be an array in the agent definition file" in error


def test_validate_definition_with_invalid_instruction_type():
    """Test validation fails when instruction is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": [1, False, None],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': instruction at index 0 must be a string in the agent definition file" in error


def test_validate_definition_with_invalid_guardrail_type():
    """Test validation fails when guardrail is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "guardrails": [1, False, None],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': guardrail at index 0 must be a string in the agent definition file" in error


def test_validate_definition_with_missing_skills():
    """Test validation fails when skills are missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                # No skills key
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent' is missing required field 'skills' in the agent definition file" in error


def test_validate_definition_with_invalid_skills_type():
    """Test validation fails when skills is not an array."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": "Not an array",
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'skills' must be an array in the agent definition file" in error


def test_validate_definition_with_invalid_skill_type():
    """Test validation fails when skill is not an object."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [1, False, None],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill at index 0 must be an object in the agent definition file" in error


def test_validate_definition_with_invalid_skill_format():
    """Test validation fails when skill data is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_name": "Skill 1",
                        "data": "Not a dictionary",
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill at index 0 must have exactly one key in the agent definition file" in error


def test_validate_definition_with_invalid_skill_data_type():
    """Test validation fails when skill data is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [{"skill_1": "Not a dictionary"}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill 'skill_1' data must be an object in the agent definition file" in error


def test_validate_definition_with_missing_skill_name():
    """Test validation fails when skill name is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [{"skill_1": {}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill 'skill_1' is missing required field 'name' in the agent definition file" in error


def test_validate_definition_with_invalid_skill_name():
    """Test validation fails when skill name is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [{"skill_1": {"name": 123}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill 'skill_1': 'name' must be a string in the agent definition file" in error


def test_validate_definition_with_missing_skill_description():
    """Test validation fails when skill description is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [{"skill_1": {"name": "Skill 1"}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1' is missing required field 'description' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_description():
    """Test validation fails when skill description is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [{"skill_1": {"name": "Skill 1", "description": 123}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill 'skill_1': 'description' must be a string in the agent definition file" in error


def test_validate_definition_with_missing_skill_source():
    """Test validation fails when skill source is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [{"skill_1": {"name": "Skill 1", "description": "Skill description"}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1' is missing required field 'source' in the agent definition file" in error
    )


def test_validate_definition_with_invalid_skill_source():
    """Test validation fails when skill source is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {"skill_1": {"name": "Skill 1", "description": "Skill description", "source": "Not a dictionary"}}
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill 'skill_1': 'source' must be an object in the agent definition file" in error


def test_validate_definition_with_missing_skill_source_path():
    """Test validation fails when skill source path is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [{"skill_1": {"name": "Skill 1", "description": "Skill description", "source": {}}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': 'source' is missing required field 'path' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_source_path():
    """Test validation fails when skill source path is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {"skill_1": {"name": "Skill 1", "description": "Skill description", "source": {"path": 123}}}
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill 'skill_1': 'source.path' must be a string in the agent definition file" in error


def test_validate_definition_with_missing_skill_source_entrypoint():
    """Test validation fails when skill source entrypoint is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {"path": "path/to/skill"},
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': 'source' is missing required field 'entrypoint' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_source_entrypoint():
    """Test validation fails when skill source entrypoint is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {"path": "path/to/skill", "entrypoint": 123},
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': 'source.entrypoint' must be a string in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_source_path_test():
    """Test validation fails when skill source path_test is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {"path": "path/to/skill", "entrypoint": "entrypoint", "path_test": 123},
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': 'source.path_test' must be a string in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_type():
    """Test validation fails when skill parameters is not a list."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": "Not a list",
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill 'skill_1': 'parameters' must be an array in the agent definition file" in error


def test_validate_definition_with_invalid_skill_parameters_item_format():
    """Test validation fails when skill parameters item is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": ["Not a dictionary"],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter at index 0 must be an object in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_format_dict_keys():
    """Test validation fails when skill parameters item is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [{"param_1": {}, "something": "else"}],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter at index 0 must have exactly one key in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_type():
    """Test validation fails when skill parameters item is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [{"param_1": "Not a dictionary"}],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1' data must be an object in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_description_missing():
    """Test validation fails when skill parameters item description is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [{"param_1": {}}],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1' is missing required field 'description' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_description_not_string():
    """Test validation fails when skill parameters item description is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [{"param_1": {"description": 123}}],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1' description must be a string in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_type_missing():
    """Test validation fails when skill parameters item type is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [{"param_1": {"description": "Parameter description"}}],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1' is missing required field 'type' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_type_not_string():
    """Test validation fails when skill parameters item type is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [{"param_1": {"description": "Parameter description", "type": 123}}],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1' type must be a string in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_type_not_allowed():
    """Test validation fails when skill parameters item type is not allowed."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [
                                {"param_1": {"description": "Parameter description", "type": "not_allowed"}}
                            ],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1' type must be one of: string, number, integer, boolean, array in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_required_type():
    """Test validation fails when skill parameters item required is not a boolean."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [
                                {
                                    "param_1": {
                                        "description": "Parameter description",
                                        "type": "string",
                                        "required": "not a boolean",
                                    }
                                }
                            ],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1' required field must be a boolean in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_contact_field_type():
    """Test validation fails when skill parameters item contact_field is not a boolean."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [
                                {
                                    "param_1": {
                                        "description": "Parameter description",
                                        "type": "string",
                                        "contact_field": "not a boolean",
                                    }
                                }
                            ],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1' contact_field must be a boolean in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_contact_field_name():
    """Test validation fails when skill parameters item contact_field is not a valid contact field name."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Instruction 1"],
                "guardrails": ["Guardrail 1"],
                "skills": [
                    {
                        "skill_1": {
                            "name": "Skill 1",
                            "description": "Skill description",
                            "source": {
                                "path": "path/to/skill",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                            "parameters": [
                                {
                                    "Param_1": {
                                        "description": "Parameter description",
                                        "type": "string",
                                        "contact_field": True,
                                    }
                                }
                            ],
                        }
                    },
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        f"Agent 'test_agent': skill 'skill_1': parameter 'Param_1' name must match the regex of a valid contact field: {CONTACT_FIELD_NAME_REGEX} in the agent definition file"
        in error
    )


def test_load_test_definition_with_yaml_error_message(mocker):
    """Test that load_test_definition correctly handles YAML load errors when the error is a string message."""
    # Create a mock error message
    error_message = "YAML parsing error: invalid syntax"

    # Mock load_yaml_file to return an error message string
    mocker.patch("weni_cli.validators.definition.load_yaml_file", return_value=(None, error_message))

    # Call load_test_definition with any path (it will be intercepted by the mock)
    result, error = load_test_definition("test_definition.yaml")

    # Verify that the function returns None for the data and the error message
    assert result is None
    assert error == error_message
    assert isinstance(error, str)


def test_load_test_definition_passes_correct_path(mocker):
    """Test that load_test_definition correctly passes the path to load_yaml_file."""
    # Mock load_yaml_file to return a dummy result but also capture the path argument
    mock_load_yaml = mocker.patch("weni_cli.validators.definition.load_yaml_file", return_value=({}, None))

    # Call load_test_definition with a specific path
    test_path = "/path/to/test_definition.yaml"
    load_test_definition(test_path)

    # Verify that load_yaml_file was called with the correct path
    mock_load_yaml.assert_called_once_with(test_path)
