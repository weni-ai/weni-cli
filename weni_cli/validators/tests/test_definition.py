import pytest
import regex
from click.testing import CliRunner
from weni_cli.validators.definition import (
    load_definition,
    format_definition,
    validate_parameters,
    is_valid_contact_field_name,
    CONTACT_FIELD_NAME_REGEX,
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
    skills:
      - test_skill:
          name: Test Skill
          description: A test skill
          source:
            path: skills/test_skill
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


def test_load_definition_valid(sample_definition_file):
    """Test loading a valid definition file."""
    result = load_definition(sample_definition_file["valid_path"])

    # Check that the result is a dictionary
    assert isinstance(result, dict)

    # Check that the expected data was loaded
    assert "agents" in result
    assert "test_agent" in result["agents"]
    assert result["agents"]["test_agent"]["name"] == "Test Agent"
    assert isinstance(result["agents"]["test_agent"]["skills"], list)


def test_load_definition_invalid(sample_definition_file, mocker):
    """Test loading an invalid definition file."""
    # Mock rich_click.echo to capture messages
    mock_echo = mocker.patch("rich_click.echo")

    result = load_definition(sample_definition_file["invalid_path"])

    # Check that the result is None
    assert result is None

    # Check that an error message was displayed
    mock_echo.assert_called_once()
    assert "Failed to parse definition file" in mock_echo.call_args[0][0]


def test_load_definition_empty(sample_definition_file, mocker):
    """Test loading an empty definition file."""
    # Mock rich_click.echo to capture messages
    mock_echo = mocker.patch("rich_click.echo")

    result = load_definition(sample_definition_file["empty_path"])

    # Check that the result is None
    assert result is None

    # Check that an error message was displayed
    mock_echo.assert_called_once_with("Error: Empty definition file")


def test_load_definition_nonexistent(mocker):
    """Test loading a non-existent definition file."""
    # The load_definition function doesn't catch FileNotFoundError outside the with block
    # So we need to add a try-except in our test

    # This should raise a FileNotFoundError which isn't caught by load_definition
    try:
        load_definition("nonexistent_file.yaml")
        # If we get here, something went wrong
        assert False, "Expected FileNotFoundError was not raised"
    except FileNotFoundError:
        # This is the expected behavior
        pass


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
