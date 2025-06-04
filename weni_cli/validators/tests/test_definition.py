import re
import pytest
import regex
from click.testing import CliRunner
from weni_cli.validators.definition import (
    AVAILABLE_COMPONENTS,
    MAX_AGENT_NAME_LENGTH,
    MAX_TOOL_NAME_LENGTH,
    load_yaml_file,
    load_agent_definition,
    format_definition,
    validate_agent_definition_schema,
    validate_active_agent_definition_schema,
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
    tools:
      - test_tool:
          name: Test Tool
          description: A test tool
          source:
            path: tools/test_tool
            entrypoint: main.TestTool
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
    tools:
      - test_tool:
          name: Test Tool
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
                "tools": [
                    {
                        "test_tool": {
                            "name": "Test Tool",
                            "description": "A test tool",
                            "source": {"path": "tools/test_tool"},
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
    assert isinstance(data["agents"]["test_agent"]["tools"], list)


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

    # Check that tools were reformatted
    tools = result["agents"]["test_agent"]["tools"]
    assert isinstance(tools, list)
    assert "key" in tools[0]
    assert "slug" in tools[0]
    assert "name" in tools[0]
    assert tools[0]["key"] == "test_tool"
    assert tools[0]["slug"] == "test-tool"
    assert tools[0]["name"] == "Test Tool"


def test_format_definition_no_tools():
    """Test formatting a definition with no tools."""
    definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent"
                # No tools
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

    # Check that tools is an empty list
    tools = result["agents"]["test_agent"]["tools"]
    assert isinstance(tools, list)
    assert len(tools) == 0


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
        tools: []
    """
    )

    # Call load_agent_definition
    result, error = load_agent_definition(str(yaml_file))

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
    assert (
        f"Agent 'test_agent': 'name' must be less than {MAX_AGENT_NAME_LENGTH} characters in the agent definition file"
        in error
    )


def test_validate_definition_without_instructions():
    """Test that a definition without instructions is valid."""
    valid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                # No instructions key
                "tools": [
                    {
                        "test_tool": {
                            "name": "Test Tool",
                            "description": "Test tool description",
                            "source": {
                                "path": "tools/test",
                                "entrypoint": "main.TestTool",
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
                "tools": [
                    {
                        "test_tool": {
                            "name": "Test Tool",
                            "description": "Test tool description",
                            "source": {
                                "path": "tools/test",
                                "entrypoint": "main.TestTool",
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
                "tools": [
                    {
                        "test_tool": {
                            "name": "Test Tool",
                            "description": "Test tool description",
                            "source": {
                                "path": "tools/test",
                                "entrypoint": "main.TestTool",
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
                "tools": [
                    {
                        "test_tool": {
                            "name": "Test Tool",
                            "description": "Test tool description",
                            "source": {
                                "path": "tools/test",
                                "entrypoint": "main.TestTool",
                            },
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': instruction at index 0 must have at least 40 characters in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_guardrails():
    """Test validation fails when guardrails is not an array."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": "Not an array",  # String instead of array
                "tools": [
                    {
                        "test_tool": {
                            "name": "Test Tool",
                            "description": "Test tool description",
                            "source": {
                                "path": "tools/test",
                                "entrypoint": "main.TestTool",
                            },
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'guardrails' must be an array in the agent definition file" in error


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
    assert (
        "Agent 'test_agent': guardrail at index 0 must have at least 40 characters in the agent definition file"
        in error
    )


def test_validate_definition_with_missing_tools():
    """Test validation fails when tools are missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                # No tools key
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent' is missing required field 'tools' in the agent definition file" in error


def test_validate_definition_with_invalid_tools_type():
    """Test validation fails when tools is not an array."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": "Not an array",
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'tools' must be an array in the agent definition file" in error


def test_validate_definition_with_invalid_tool_type():
    """Test validation fails when tool is not an object."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [1, False, None],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool at index 0 must be an object in the agent definition file" in error


def test_validate_definition_with_invalid_tool_format():
    """Test validation fails when tool data is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_name": "Tool 1",
                        "data": "Not a dictionary",
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool at index 0 must have exactly one key in the agent definition file" in error


def test_validate_definition_with_invalid_tool_data_type():
    """Test validation fails when tool data is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [{"tool_1": "Not a dictionary"}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool 'tool_1' data must be an object in the agent definition file" in error


def test_validate_definition_with_missing_tool_name():
    """Test validation fails when tool name is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [{"tool_1": {}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool 'tool_1' is missing required field 'name' in the agent definition file" in error


def test_validate_definition_with_invalid_tool_name():
    """Test validation fails when tool name is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [{"tool_1": {"name": 123}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool 'tool_1': 'name' must be a string in the agent definition file" in error


def test_validate_definition_with_invalid_tool_name_length():
    """Test validation fails when tool name is longer than the maximum allowed length."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Agent Name",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool Name with a really really really really really really really really really really really really long name"
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        f"Agent 'test_agent': tool 'tool_1': 'name' must be less than {MAX_TOOL_NAME_LENGTH} characters in the agent definition file"
        in error
    )


def test_validate_definition_with_missing_tool_description():
    """Test validation fails when tool description is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [{"tool_1": {"name": "Tool 1"}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': tool 'tool_1' is missing required field 'description' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_description():
    """Test validation fails when tool description is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [{"tool_1": {"name": "Tool 1", "description": 123}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool 'tool_1': 'description' must be a string in the agent definition file" in error


def test_validate_definition_with_missing_tool_source():
    """Test validation fails when tool source is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [{"tool_1": {"name": "Tool 1", "description": "Tool description"}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool 'tool_1' is missing required field 'source' in the agent definition file" in error


def test_validate_definition_with_invalid_tool_source():
    """Test validation fails when tool source is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {"tool_1": {"name": "Tool 1", "description": "Tool description", "source": "Not a dictionary"}}
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool 'tool_1': 'source' must be an object in the agent definition file" in error


def test_validate_definition_with_missing_tool_source_path():
    """Test validation fails when tool source path is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [{"tool_1": {"name": "Tool 1", "description": "Tool description", "source": {}}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': tool 'tool_1': 'source' is missing required field 'path' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_source_path():
    """Test validation fails when tool source path is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [{"tool_1": {"name": "Tool 1", "description": "Tool description", "source": {"path": 123}}}],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': tool 'tool_1': 'source.path' must be a string in the agent definition file" in error


def test_validate_definition_with_missing_tool_source_entrypoint():
    """Test validation fails when tool source entrypoint is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {"path": "path/to/tool"},
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': tool 'tool_1': 'source' is missing required field 'entrypoint' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_source_entrypoint():
    """Test validation fails when tool source entrypoint is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {"path": "path/to/tool", "entrypoint": 123},
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': tool 'tool_1': 'source.entrypoint' must be a string in the agent definition file" in error
    )


def test_validate_definition_with_invalid_tool_source_path_test():
    """Test validation fails when tool source path_test is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {"path": "path/to/tool", "entrypoint": "entrypoint", "path_test": 123},
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'test_agent': tool 'tool_1': 'source.path_test' must be a string in the agent definition file" in error
    )


def test_validate_definition_with_invalid_tool_parameters_type():
    """Test validation fails when tool parameters is not a list."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
    assert "Agent 'test_agent': tool 'tool_1': 'parameters' must be an array in the agent definition file" in error


def test_validate_definition_with_invalid_tool_parameters_item_format():
    """Test validation fails when tool parameters item is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter at index 0 must be an object in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_format_dict_keys():
    """Test validation fails when tool parameters item is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter at index 0 must have exactly one key in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_type():
    """Test validation fails when tool parameters item is not a dictionary."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1' data must be an object in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_description_missing():
    """Test validation fails when tool parameters item description is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1' is missing required field 'description' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_description_not_string():
    """Test validation fails when tool parameters item description is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1' description must be a string in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_type_missing():
    """Test validation fails when tool parameters item type is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1' is missing required field 'type' in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_type_not_string():
    """Test validation fails when tool parameters item type is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1' type must be a string in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_type_not_allowed():
    """Test validation fails when tool parameters item type is not allowed."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1' type must be one of: string, number, integer, boolean, array in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_required_type():
    """Test validation fails when tool parameters item required is not a boolean."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1' required field must be a boolean in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_contact_field_type():
    """Test validation fails when tool parameters item contact_field is not a boolean."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1' contact_field must be a boolean in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_contact_field_name():
    """Test validation fails when tool parameters item contact_field is not a valid contact field name."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        f"Agent 'test_agent': tool 'tool_1': parameter 'Param_1' name must match the regex of a valid contact field: {re.escape(ContactFieldValidator.CONTACT_FIELD_NAME_REGEX)} in the agent definition file"  # noqa W605
        in error
    )


def test_validate_definition_with_invalid_tool_parameters_item_contact_field_name_length():
    """Test validation fails when tool parameters item contact_field is not a valid contact field name."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'param_1_with_a_very_long_name_that_exceeds_the_maximum_length_of_36_characters' name must be 36 characters or less in the agent definition file"
        in error
    )


def test_validate_definition_with_valid_tool_parameters_item_contact_field_name():
    """Test validation passes when tool parameters item contact_field is a valid contact field name."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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


def test_validate_definition_with_invalid_tool_parameters_item_contact_field_name_reserved():
    """Test validation fails when tool parameters item contact_field is a reserved contact field name."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "instructions": SAMPLE_INSTRUCTIONS,
                "guardrails": SAMPLE_GUARDRAILS,
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
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
        "Agent 'test_agent': tool 'tool_1': parameter 'id' name must not be a reserved contact field name in the agent definition file"
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
    assert "Agent 'test_agent': 'components' must be an array in the agent definition file" in error


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
    assert "Agent 'test_agent': component at index 0 must be an object in the agent definition file" in error


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
    assert "Agent 'test_agent': component at index 0 must have a 'type' field in the agent definition file" in error


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
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                        }
                    }
                ],
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
                "tools": [
                    {
                        "tool_1": {
                            "name": "Tool 1",
                            "description": "Tool description",
                            "source": {
                                "path": "path/to/tool",
                                "entrypoint": "entrypoint",
                                "path_test": "path/to/test",
                            },
                        }
                    }
                ],
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


def test_validate_definition_with_valid_credentials():
    """Test validation passes when credentials are valid."""
    valid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "credentials": {
                    "api_key": {"label": "API Key", "placeholder": "Enter your API key", "is_confidential": True},
                    "username": {"label": "Username", "placeholder": "Enter your username"},
                },
                "tools": [
                    {
                        "test_tool": {
                            "name": "Test Tool",
                            "description": "Test tool description",
                            "source": {
                                "path": "tools/test",
                                "entrypoint": "main.TestTool",
                            },
                        }
                    }
                ],
            }
        }
    }

    error = validate_agent_definition_schema(valid_definition)
    assert error is None


def test_validate_definition_with_invalid_credentials_type():
    """Test validation fails when credentials is not an object."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "credentials": "Not an object",  # String instead of object
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
    assert "Agent 'test_agent': 'credentials' must be an object in the agent definition file" in error


def test_validate_definition_with_invalid_credential_value_type():
    """Test validation fails when credential value is not an object."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "credentials": {"api_key": "Not an object"},  # String instead of object
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
    assert "Agent 'test_agent': value for credential 'api_key' must be an object in the agent definition file" in error


def test_validate_definition_with_missing_credential_label():
    """Test validation fails when credential label is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "credentials": {
                    "api_key": {
                        # No label
                        "placeholder": "Enter your API key"
                    }
                },
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
    assert "Agent 'test_agent': 'label' for credential 'api_key' is missing in the agent definition file" in error


def test_validate_definition_with_invalid_credential_label_type():
    """Test validation fails when credential label is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "credentials": {
                    "api_key": {"label": 123, "placeholder": "Enter your API key"}  # Number instead of string
                },
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
    assert (
        "Agent 'test_agent': 'label' for credential 'api_key' must be a string in the agent definition file" in error
    )


def test_validate_definition_with_missing_credential_placeholder():
    """Test validation fails when credential placeholder is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "credentials": {
                    "api_key": {
                        "label": "API Key",
                        # No placeholder
                    }
                },
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
    assert (
        "Agent 'test_agent': 'placeholder' for credential 'api_key' is missing in the agent definition file" in error
    )


def test_validate_definition_with_invalid_credential_placeholder_type():
    """Test validation fails when credential placeholder is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "credentials": {"api_key": {"label": "API Key", "placeholder": 123}},  # Number instead of string
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
    assert (
        "Agent 'test_agent': 'placeholder' for credential 'api_key' must be a string in the agent definition file"
        in error
    )


def test_validate_definition_with_invalid_credential_is_confidential_type():
    """Test validation fails when credential is_confidential is not a boolean."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test description",
                "credentials": {
                    "api_key": {
                        "label": "API Key",
                        "placeholder": "Enter your API key",
                        "is_confidential": "true",  # String instead of boolean
                    }
                },
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
    assert (
        "Agent 'test_agent': 'is_confidential' for credential 'api_key' must be a boolean in the agent definition file"
        in error
    )


def test_validate_definition_with_valid_rules_type():
    """Test validation passes when rules is an dictionary and contains two rules, each rule is an object with template and source, with source having entrypoint and path."""
    valid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with rules",
                "language": "pt_BR",
                "rules": {
                    "first_rule": {
                        "template": "first_template",
                        "display_name": "First Rule",
                        "start_condition": "contact.name is not None",
                        "source": {"entrypoint": "main.FirstRule", "path": "rules/first_rule"},
                    },
                    "second_rule": {
                        "template": "second_template",
                        "display_name": "Second Rule",
                        "start_condition": "contact.field_value == 'test'",
                        "source": {
                            "entrypoint": "main.SecondRule",
                            "path": "tools/second_rule",
                        },
                    },
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(valid_definition)
    assert error is None


def test_validate_definition_with_invalid_rules_type():
    """Test validation fails when rules is not a dictionary."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid rules",
                "language": "pt_BR",
                "rules": "not a dictionary",
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'rules' must be an object in the agent definition file" in error


def test_validate_definition_with_invalid_rule_data_type():
    """Test validation fails when rule data is not a dictionary."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid rule data",
                "language": "pt_BR",
                "rules": {"invalid_rule": "not a dictionary"},
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule' data must be an object in the agent definition file" in error


def test_validate_definition_with_missing_rule_template():
    """Test validation fails when rule template is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing rule template",
                "language": "pt_BR",
                "rules": {
                    "invalid_rule": {
                        # No template
                        "source": {"entrypoint": "main.Rule", "path": "rules/rule"}
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule' is missing required field 'template'" in error


def test_validate_definition_with_invalid_rule_template_type():
    """Test validation fails when rule template is not a string."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid rule template type",
                "language": "pt_BR",
                "rules": {
                    "invalid_rule": {
                        "template": 123,  # Not a string
                        "source": {"entrypoint": "main.Rule", "path": "rules/rule"},
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule': 'template' must be a string" in error


def test_validate_definition_with_missing_rule_source():
    """Test validation fails when rule source is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing rule source",
                "language": "pt_BR",
                "rules": {
                    "invalid_rule": {
                        "template": "template"
                        # No source
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule' is missing required field 'source'" in error


def test_validate_definition_with_invalid_rule_source_type():
    """Test validation fails when rule source is not a dictionary."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid rule source type",
                "language": "pt_BR",
                "rules": {"invalid_rule": {"template": "template", "source": "not a dictionary"}},  # Not a dictionary
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule': 'source' must be an object" in error


def test_validate_definition_with_missing_rule_source_path():
    """Test validation fails when rule source path is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing rule source path",
                "language": "pt_BR",
                "rules": {
                    "invalid_rule": {
                        "template": "template",
                        "source": {
                            "entrypoint": "main.Rule"
                            # No path
                        },
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule': 'source' is missing required field 'path'" in error


def test_validate_definition_with_invalid_rule_source_path_type():
    """Test validation fails when rule source path is not a string."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid rule source path type",
                "language": "pt_BR",
                "rules": {
                    "invalid_rule": {
                        "template": "template",
                        "source": {"entrypoint": "main.Rule", "path": 123},  # Not a string
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule': 'source.path' must be a string" in error


def test_validate_definition_with_missing_rule_source_entrypoint():
    """Test validation fails when rule source entrypoint is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing rule source entrypoint",
                "language": "pt_BR",
                "rules": {
                    "invalid_rule": {
                        "template": "template",
                        "source": {
                            "path": "rules/rule"
                            # No entrypoint
                        },
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule': 'source' is missing required field 'entrypoint'" in error


def test_validate_definition_with_invalid_rule_source_entrypoint_type():
    """Test validation fails when rule source entrypoint is not a string."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid rule source entrypoint type",
                "language": "pt_BR",
                "rules": {
                    "invalid_rule": {
                        "template": "template",
                        "source": {"path": "rules/rule", "entrypoint": 123},  # Not a string
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'invalid_rule': 'source.entrypoint' must be a string" in error


def test_validate_definition_with_valid_preprocessing_type():
    """Test validation passes when pre-processing is an dictionary and contains source, with source having entrypoint and path."""
    valid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with valid preprocessing",
                "language": "pt_BR",
                "pre-processing": {
                    "source": {"entrypoint": "preprocessing.PreProcessor", "path": "pre_processor/processor"},
                    "result_examples_file": "examples.json",
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(valid_definition)
    assert error is None


def test_validate_definition_with_invalid_preprocessing_type():
    """Test validation fails when pre-processing is not a dictionary."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid preprocessing type",
                "language": "pt_BR",
                "pre-processing": "not a dictionary",
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'pre-processing' must be an object in the agent definition file" in error


def test_validate_definition_with_missing_preprocessing_source():
    """Test validation fails when pre-processing source is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing preprocessing source",
                "language": "pt_BR",
                "pre-processing": {
                    # Missing source
                    "result_examples_file": "examples.json"
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'pre-processing' is missing required field 'source'" in error


def test_validate_definition_with_invalid_preprocessing_source_type():
    """Test validation fails when pre-processing source is not a dictionary."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid preprocessing source type",
                "language": "pt_BR",
                "pre-processing": {"source": "not a dictionary", "result_examples_file": "examples.json"},
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'pre-processing.source' must be an object in the agent definition file" in error


def test_validate_definition_with_missing_preprocessing_source_path():
    """Test validation fails when pre-processing source path is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing preprocessing source path",
                "language": "pt_BR",
                "pre-processing": {
                    "source": {
                        "entrypoint": "preprocessing.PreProcessor"
                        # Missing path
                    },
                    "result_examples_file": "examples.json",
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'pre-processing.source' is missing required field 'path'" in error


def test_validate_definition_with_invalid_preprocessing_source_path_type():
    """Test validation fails when pre-processing source path is not a string."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid preprocessing source path type",
                "language": "pt_BR",
                "pre-processing": {
                    "source": {"entrypoint": "preprocessing.PreProcessor", "path": 123},  # Not a string
                    "result_examples_file": "examples.json",
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'pre-processing.source.path' must be a string in the agent definition file" in error


def test_validate_definition_with_missing_preprocessing_source_entrypoint():
    """Test validation fails when pre-processing source entrypoint is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing preprocessing source entrypoint",
                "language": "pt_BR",
                "pre-processing": {
                    "source": {
                        "path": "pre_processor/processor"
                        # Missing entrypoint
                    },
                    "result_examples_file": "examples.json",
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'pre-processing.source' is missing required field 'entrypoint'" in error


def test_validate_definition_with_invalid_preprocessing_source_entrypoint_type():
    """Test validation fails when pre-processing source entrypoint is not a string."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid preprocessing source entrypoint type",
                "language": "pt_BR",
                "pre-processing": {
                    "source": {"path": "pre_processor/processor", "entrypoint": 123},  # Not a string
                    "result_examples_file": "examples.json",
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert (
        "Agent 'my_agent': 'pre-processing.source.entrypoint' must be a string in the agent definition file" in error
    )


def test_validate_definition_with_missing_preprocessing_result_examples_file():
    """Test validation fails when pre-processing result_examples_file is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing preprocessing result_examples_file",
                "language": "pt_BR",
                "pre-processing": {
                    "source": {"path": "pre_processor/processor", "entrypoint": "preprocessing.PreProcessor"}
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'pre-processing' is missing required field 'result_examples_file'" in error


def test_validate_definition_with_invalid_preprocessing_result_examples_file_suffix():
    """Test validation fails when pre-processing result_examples_file doesn't end with .json."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid preprocessing result_examples_file suffix",
                "language": "pt_BR",
                "pre-processing": {
                    "source": {
                        "path": "pre_processor/processor",
                        "entrypoint": "preprocessing.PreProcessor",
                    },
                    "result_examples_file": "examples.txt",  # Not a .json file
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': 'pre-processing.result_examples_file' must be a string with a .json in suffix" in error


def test_validate_definition_with_valid_complete_active_agent():
    """Test validation passes with a complete valid active agent definition containing all fields."""
    valid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test Description",
                "language": "pt_BR",  # Added required language field
                "webhook_example": ["example1.json", "example2.json"],
                "rules": {
                    "test_rule": {
                        "template": "rule_template",
                        "display_name": "Test Rule",
                        "start_condition": "contact.name is not None",
                        "source": {
                            "path": "rules/test_rule",
                            "entrypoint": "main.TestRule",
                        },
                    }
                },
                "pre-processing": {
                    "source": {
                        "path": "pre_processor/processor",
                        "entrypoint": "preprocessing.PreProcessor",
                    },
                    "result_examples_file": "examples.json",
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(valid_definition)
    assert error is None


def test_validate_definition_with_missing_language():
    """Test validation fails when language field is missing."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test Description",
                "rules": {
                    "test_rule": {
                        "template": "rule_template",
                        "display_name": "Test Rule",
                        "start_condition": "contact.name is not None",
                        "source": {
                            "path": "rules/test_rule",
                            "entrypoint": "main.TestRule",
                        },
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent' is missing required field 'language' in the agent definition file" in error


def test_validate_definition_with_invalid_language_type():
    """Test validation fails when language is not a string."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test Description",
                "language": 123,  # Not a string
                "rules": {
                    "test_rule": {
                        "template": "rule_template",
                        "display_name": "Test Rule",
                        "start_condition": "contact.name is not None",
                        "source": {
                            "path": "rules/test_rule",
                            "entrypoint": "main.TestRule",
                        },
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'language' must be a string" in error


def test_validate_definition_with_invalid_language_code():
    """Test validation fails when language code is not in the allowed list."""
    invalid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test Description",
                "language": "invalid_lang",  # Invalid language code
                "rules": {
                    "test_rule": {
                        "template": "rule_template",
                        "display_name": "Test Rule",
                        "start_condition": "contact.name is not None",
                        "source": {
                            "path": "rules/test_rule",
                            "entrypoint": "main.TestRule",
                        },
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'test_agent': 'language' must be one of the following values:" in error


def test_validate_definition_with_valid_language():
    """Test validation passes when language is a valid language code."""
    valid_definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test Description",
                "language": "pt_BR",
                "rules": {
                    "test_rule": {
                        "template": "rule_template",
                        "display_name": "Test Rule",
                        "start_condition": "contact.name is not None",
                        "source": {
                            "path": "rules/test_rule",
                            "entrypoint": "main.TestRule",
                        },
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(valid_definition)
    assert error is None


def test_validate_definition_with_missing_rule_start_condition():
    """Test validation fails when rule start_condition is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing rule start_condition",
                "language": "pt_BR",
                "rules": {
                    "test_rule": {
                        "template": "template",
                        "display_name": "Test Rule",
                        "source": {"path": "rules/rule", "entrypoint": "main.Rule"},
                        # Missing start_condition
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'test_rule' is missing required field 'start_condition'" in error


def test_validate_definition_with_invalid_rule_start_condition_type():
    """Test validation fails when rule start_condition is not a string."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid rule start_condition type",
                "language": "pt_BR",
                "rules": {
                    "test_rule": {
                        "template": "template",
                        "display_name": "Test Rule",
                        "start_condition": 123,  # Not a string
                        "source": {"path": "rules/rule", "entrypoint": "main.Rule"},
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'test_rule': 'start_condition' must be a string" in error


def test_validate_definition_with_missing_rule_display_name():
    """Test validation fails when rule display_name is missing."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with missing rule display_name",
                "language": "pt_BR",
                "rules": {
                    "test_rule": {
                        "template": "template",
                        "start_condition": "contact.name is not None",
                        "source": {"path": "rules/rule", "entrypoint": "main.Rule"},
                        # Missing display_name
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'test_rule' is missing required field 'display_name'" in error


def test_validate_definition_with_invalid_rule_display_name_type():
    """Test validation fails when rule display_name is not a string."""
    invalid_definition = {
        "agents": {
            "my_agent": {
                "name": "My Agent",
                "description": "A test agent with invalid rule display_name type",
                "language": "pt_BR",
                "rules": {
                    "test_rule": {
                        "template": "template",
                        "display_name": 123,  # Not a string
                        "start_condition": "contact.name is not None",
                        "source": {"path": "rules/rule", "entrypoint": "main.Rule"},
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(invalid_definition)
    assert error is not None
    assert "Agent 'my_agent': rule 'test_rule': 'display_name' must be a string" in error


def test_validate_definition_with_whitespace_in_template():
    """Test that a template with whitespace is rejected."""
    definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test Description",
                "language": "pt_BR",
                "rules": {
                    "test_rule": {
                        "template": "template with spaces",
                        "source": {"path": "test/path", "entrypoint": "test.entrypoint"},
                        "start_condition": "test condition",
                        "display_name": "Test Rule",
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(definition)
    assert error is not None
    assert "Agent 'test_agent': rule 'test_rule': 'template' must not contain whitespace" in error
    assert "Use underscores instead in the agent definition file" in error


def test_validate_definition_with_valid_template_name():
    """Test that a template without whitespace is accepted."""
    definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "description": "Test Description",
                "language": "pt_BR",
                "rules": {
                    "test_rule": {
                        "template": "template_without_spaces",
                        "source": {"path": "test/path", "entrypoint": "test.entrypoint"},
                        "start_condition": "test condition",
                        "display_name": "Test Rule",
                    }
                },
            }
        }
    }

    error = validate_active_agent_definition_schema(definition)
    assert error is None
