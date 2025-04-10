import re
import pytest
import regex
from click.testing import CliRunner
from weni_cli.validators.definition import (
    AVAILABLE_COMPONENTS,
    MAX_AGENT_NAME_LENGTH,
    MAX_SKILL_NAME_LENGTH,
    load_yaml_file,
    load_agent_definition,
    format_definition,
    validate_agent_definition_schema,
    load_test_definition,
    ContactFieldValidator,
)

SAMPLE_INSTRUCTIONS = [
    "This is a test instruction with more than 40 characters",
    "This is another test instruction with more than 40 characters",
    "This is a third test instruction with more than 40 characters",
]

SAMPLE_GUARDRAILS = [
    "This is a test guardrail with more than 40 characters",
    "This is another test guardrail with more than 40 characters",
]


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


def test_is_valid_contact_field_name_valid():
    """Test valid contact field names."""
    valid_names = ["valid", "valid123", "valid_name", "a123_456"]

    for name in valid_names:
        assert ContactFieldValidator.has_valid_contact_field_name(name) is True


def test_is_valid_contact_field_name_invalid():
    """Test invalid contact field names."""
    invalid_names = ["123invalid", "Invalid", "invalid-name", "_invalid", "invalid.name"]

    for name in invalid_names:
        assert ContactFieldValidator.has_valid_contact_field_name(name) is False


def test_contact_field_regex_pattern():
    """Test the contact field regex pattern directly."""
    # This test ensures the regex pattern matches what we expect
    valid_names = ["valid", "valid123", "valid_name", "a123_456"]
    invalid_names = ["123invalid", "Invalid", "invalid-name", "_invalid", "invalid.name"]

    for name in valid_names:
        assert regex.match(ContactFieldValidator.CONTACT_FIELD_NAME_REGEX, name, regex.V0) is not None

    for name in invalid_names:
        assert regex.match(ContactFieldValidator.CONTACT_FIELD_NAME_REGEX, name, regex.V0) is None


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


def test_load_agent_definition_fails_on_empty_file(mocker, tmpdir):
    """Test that load_agent_definition returns error when file is empty."""
    yaml_file = tmpdir.join("empty_definition.yaml")
    yaml_file.write("")

    result, error = load_agent_definition(str(yaml_file))
    assert result is None
    assert error is not None
    assert "Empty definition file" in str(error)


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


def test_validate_definition_with_invalid_agent_name_length():
    """Test that a definition with an invalid agent name length is invalid."""
    invalid_definition = {"agents": {"test_agent": {"name": "a" * 83}}}

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert f"Agent 'test_agent': 'name' must be less than {MAX_AGENT_NAME_LENGTH} characters in the agent definition file" in error


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
                "instructions": SAMPLE_INSTRUCTIONS,
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


def test_validate_definition_file_with_short_instruction():
    """Test validation fails when instruction is shorter than the minimum allowed length."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": ["Short instruction"],
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
    assert "Agent 'test_agent': instruction at index 0 must have at least 40 characters in the agent definition file" in error


def test_validate_definition_with_invalid_guardrails():
    """Test validation fails when guardrails is not an array."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
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


def test_validate_agent_definition_with_short_guardrail():
    """Test validation fails when guardrail is shorter than the minimum allowed length."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": ["Short guardrail"],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': guardrail at index 0 must have at least 40 characters in the agent definition file" in error


def test_validate_definition_with_missing_skills():
    """Test validation fails when skills are missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "skills": [{"skill_1": {"name": 123}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': skill 'skill_1': 'name' must be a string in the agent definition file" in error


def test_validate_definition_with_invalid_skill_name_length():
    """Test validation fails when skill name is longer than the maximum allowed length."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Agent Name",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "skills": [{"skill_1": {"name": "kill Name with a really really really really really really really really really really really really long name"}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert f"Agent 'test_agent': skill 'skill_1': 'name' must be less than {MAX_SKILL_NAME_LENGTH} characters in the agent definition file" in error


def test_validate_definition_with_missing_skill_description():
    """Test validation fails when skill description is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
        f"Agent 'test_agent': skill 'skill_1': parameter 'Param_1' name must match the regex of a valid contact field: {re.escape(ContactFieldValidator.CONTACT_FIELD_NAME_REGEX)} in the agent definition file" # noqa W605
        in error
    )


def test_validate_definition_with_invalid_skill_parameters_item_contact_field_name_length():
    """Test validation fails when skill parameters item contact_field is not a valid contact field name."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                                    "param_1_with_a_very_long_name_that_exceeds_the_maximum_length_of_36_characters": {
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
        "Agent 'test_agent': skill 'skill_1': parameter 'param_1_with_a_very_long_name_that_exceeds_the_maximum_length_of_36_characters' name must be 36 characters or less in the agent definition file"
        in error
    )


def test_validate_definition_with_valid_skill_parameters_item_contact_field_name():
    """Test validation passes when skill parameters item contact_field is a valid contact field name."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
    assert error is None


def test_validate_definition_with_invalid_skill_parameters_item_contact_field_name_reserved():
    """Test validation fails when skill parameters item contact_field is a reserved contact field name."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
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
                                    "id": {
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
        "Agent 'test_agent': skill 'skill_1': parameter 'id' name must not be a reserved contact field name in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_components_value():
    """Test validation fails when components value is not a list."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "components": "not a list",
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': 'components' must be an array in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_component_value_type():
    """Test validation fails when component value is not a list."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "components": ["catalog"],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': component at index 0 must be an object in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_component_type_missing():
    """Test validation fails when component type is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "components": [{"not_type": "cta_message"}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': component at index 0 must have a 'type' field in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_component_type():
    """Test validation fails when component type is not a valid component type."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "components": [{"type": "not_a_valid_component_type"}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        f"Agent 'test_agent': component at index 0 must have a 'type' field with one of the following values: {', '.join(AVAILABLE_COMPONENTS)} in the agent definition file"  # noqa: F821
        in error
    )


def test_validate_definition_with_invalid_component_instructions():
    """Test validation fails when component instructions is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "components": [{"type": "cta_message", "instructions": 1}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': component at index 0 must have a 'instructions' field with a string value in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_component_instructions_type():
    """Test validation fails when component instructions is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "components": [{"type": "cta_message", "instructions": 1}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': component at index 0 must have a 'instructions' field with a string value in the agent definition file"
        in error
    )


def test_validate_definition_with_valid_component_instructions():
    """Test validation passes when component instructions is a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "components": [{"type": "cta_message", "instructions": "test"}],
                "skills": [{"skill_1": {"name": "Skill 1", "description": "Skill description", "source": {"path": "path/to/skill", "entrypoint": "entrypoint", "path_test": "path/to/test"}}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is None


def test_validate_definition_with_valid_component_and_no_instructions():
    """Test validation passes when component has no instructions."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "components": [{"type": "cta_message"}],
                "skills": [{"skill_1": {"name": "Skill 1", "description": "Skill description", "source": {"path": "path/to/skill", "entrypoint": "entrypoint", "path_test": "path/to/test"}}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is None


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
