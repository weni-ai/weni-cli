import pytest
from click.testing import CliRunner

from weni_cli.validators.ticketer_definition import (
    AVAILABLE_TICKETER_TYPES,
    MAX_TICKETER_NAME_LENGTH,
    load_ticketer_definition,
    validate_ticketer_definition_schema,
)


@pytest.fixture
def sample_definition_file():
    """Create a sample ticketer definition file for testing."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("valid_ticketer_definition.yaml", "w") as f:
            f.write(
                """
ticketers:
  - name: org support
    ticketer_type: generic
    config:
      base_url: https://example.com
      api_token: test-api-token
      webhook_secret: test-webhook-secret
      project_name: org support
                """
            )

        with open("empty_ticketer_definition.yaml", "w") as f:
            f.write("")

        yield {
            "valid_path": "valid_ticketer_definition.yaml",
            "empty_path": "empty_ticketer_definition.yaml",
        }


@pytest.fixture
def valid_ticketer_definition():
    """Return a valid ticketer definition dictionary."""
    return {
        "ticketers": [
            {
                "name": "org support",
                "ticketer_type": "generic",
                "config": {
                    "base_url": "https://example.com",
                    "api_token": "test-api-token",
                    "webhook_secret": "test-webhook-secret",
                },
            }
        ]
    }


class TestValidateTicketerDefinitionSchema:
    """Tests for validate_ticketer_definition_schema function."""

    def test_valid_ticketer_definition(self, valid_ticketer_definition):
        error = validate_ticketer_definition_schema(valid_ticketer_definition)
        assert error is None

    def test_valid_ticketer_definition_with_skip_hmac(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
        del data["ticketers"][0]["config"]["webhook_secret"]
        data["ticketers"][0]["config"]["skip_webhook_hmac"] = "true"
        error = validate_ticketer_definition_schema(data)
        assert error is None

    def test_missing_ticketers_key(self):
        error = validate_ticketer_definition_schema({})
        assert error == "Missing required root key 'ticketers' in the ticketer definition file"

    def test_ticketers_not_array(self):
        error = validate_ticketer_definition_schema({"ticketers": {}})
        assert error == "'ticketers' must be an array in the ticketer definition file"

    def test_empty_ticketers_array(self):
        error = validate_ticketer_definition_schema({"ticketers": []})
        assert error == "No ticketers defined in the ticketer definition file"

    def test_ticketer_not_object(self):
        error = validate_ticketer_definition_schema({"ticketers": ["not an object"]})
        assert error == "Ticketer at index 0 must be an object in the ticketer definition file"

    def test_missing_name(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        del data["ticketers"][0]["name"]
        error = validate_ticketer_definition_schema(data)
        assert error == "Ticketer at index 0 is missing required field 'name' in the ticketer definition file"

    def test_name_too_long(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["name"] = "x" * (MAX_TICKETER_NAME_LENGTH + 1)
        error = validate_ticketer_definition_schema(data)
        assert (
            error
            == f"Ticketer at index 0: 'name' must be less than {MAX_TICKETER_NAME_LENGTH} characters in the ticketer definition file"
        )

    def test_missing_ticketer_type(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        del data["ticketers"][0]["ticketer_type"]
        error = validate_ticketer_definition_schema(data)
        assert (
            error
            == "Ticketer at index 0 is missing required field 'ticketer_type' in the ticketer definition file"
        )

    def test_invalid_ticketer_type(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["ticketer_type"] = "invalid"
        error = validate_ticketer_definition_schema(data)
        assert (
            error
            == f"Ticketer at index 0: 'ticketer_type' must be one of: {', '.join(AVAILABLE_TICKETER_TYPES)} in the ticketer definition file"
        )

    def test_missing_config(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        del data["ticketers"][0]["config"]
        error = validate_ticketer_definition_schema(data)
        assert error == "Ticketer at index 0 is missing required field 'config' in the ticketer definition file"

    def test_missing_base_url(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
        del data["ticketers"][0]["config"]["base_url"]
        error = validate_ticketer_definition_schema(data)
        assert (
            error
            == "Ticketer at index 0: 'config' is missing required field 'base_url' in the ticketer definition file"
        )

    def test_invalid_base_url(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
        data["ticketers"][0]["config"]["base_url"] = "not-a-valid-url"
        error = validate_ticketer_definition_schema(data)
        assert (
            error
            == "Ticketer at index 0: 'config.base_url' must be a valid URL starting with http:// or https:// in the ticketer definition file"
        )

    def test_missing_webhook_secret_without_skip_hmac(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
        del data["ticketers"][0]["config"]["webhook_secret"]
        error = validate_ticketer_definition_schema(data)
        assert (
            error
            == "Ticketer at index 0: 'config.webhook_secret' is required unless "
            "'config.skip_webhook_hmac' is set to true, 1 or yes in the ticketer definition file"
        )

    def test_config_value_not_string(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
        data["ticketers"][0]["config"]["api_token"] = 123
        error = validate_ticketer_definition_schema(data)
        assert (
            error == "Ticketer at index 0: 'config.api_token' must be a string in the ticketer definition file"
        )

    def test_unknown_config_field(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
        data["ticketers"][0]["config"]["unknown_field"] = "value"
        error = validate_ticketer_definition_schema(data)
        assert (
            error
            == "Ticketer at index 0: 'config.unknown_field' is not a recognized field in the ticketer definition file"
        )


class TestLoadTicketerDefinition:
    """Tests for load_ticketer_definition function."""

    def test_load_valid_ticketer_definition(self, sample_definition_file):
        data, error = load_ticketer_definition(sample_definition_file["valid_path"])
        assert error is None
        assert "ticketers" in data

    def test_load_empty_ticketer_definition(self, sample_definition_file):
        data, error = load_ticketer_definition(sample_definition_file["empty_path"])
        assert data is None
        assert str(error) == "Empty definition file"

    def test_load_nonexistent_file(self):
        data, error = load_ticketer_definition("nonexistent.yaml")
        assert data is None
        assert error is not None
