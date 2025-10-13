import pytest
from click.testing import CliRunner
from weni_cli.validators.channel_definition import (
    validate_channel_definition_schema,
    load_channel_definition,
    MAX_CHANNEL_NAME_LENGTH,
    AVAILABLE_CHANNEL_TYPES,
    AVAILABLE_SCHEMES,
    AVAILABLE_SEND_METHODS,
    AVAILABLE_CONTENT_TYPES,
)


@pytest.fixture
def sample_definition_file():
    """Create a sample definition file for testing."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a valid definition file
        with open("valid_channel_definition.yaml", "w") as f:
            f.write(
                """
channels:
  - name: Test Channel
    channel_type: E2
    schemes:
      - external
    config:
      mo_response_content_type: application/json
      mo_response: ""
      mt_response_check: ""
      send_url: https://example.com/send_msg
      send_method: POST
      send_template: '{"chat_id":"{{.urn_path}}","text":"{{.text}}","parse_mode":"Markdown"}'
      content_type: application/x-www-form-urlencoded
      receive_template: '{"messages":[{"urn_path":"{{.message.from.id}}","text":"{{.message.text}}","contact_name":"{{.message.from.username}}","id":"{{.message.message_id}}"}]}'
      send_authorization: ""
                """
            )

        # Create an empty definition file
        with open("empty_channel_definition.yaml", "w") as f:
            f.write("")

        yield {
            "valid_path": "valid_channel_definition.yaml",
            "empty_path": "empty_channel_definition.yaml",
        }


@pytest.fixture
def valid_channel_definition():
    """Return a valid channel definition dictionary."""
    return {
        "channels": [
            {
                "name": "Test Channel",
                "channel_type": "E2",
                "schemes": ["external"],
                "config": {
                    "mo_response_content_type": "application/json",
                    "mo_response": "",
                    "mt_response_check": "",
                    "send_url": "https://example.com/send_msg",
                    "send_method": "POST",
                    "send_template": '{"chat_id":"{{.urn_path}}","text":"{{.text}}","parse_mode":"Markdown"}',
                    "content_type": "application/x-www-form-urlencoded",
                    "receive_template": '{"messages":[{"urn_path":"{{.message.from.id}}","text":"{{.message.text}}","contact_name":"{{.message.from.username}}","id":"{{.message.message_id}}"}]}',
                    "send_authorization": "",
                },
            }
        ]
    }


class TestValidateChannelDefinitionSchema:
    """Tests for validate_channel_definition_schema function."""

    def test_valid_channel_definition(self, valid_channel_definition):
        """Test validation with a valid channel definition."""
        error = validate_channel_definition_schema(valid_channel_definition)
        assert error is None

    def test_missing_channels_key(self):
        """Test validation fails when 'channels' key is missing."""
        data = {}
        error = validate_channel_definition_schema(data)
        assert error == "Missing required root key 'channels' in the channel definition file"

    def test_channels_not_array(self):
        """Test validation fails when 'channels' is not an array."""
        data = {"channels": {}}
        error = validate_channel_definition_schema(data)
        assert error == "'channels' must be an array in the channel definition file"

    def test_empty_channels_array(self):
        """Test validation fails when 'channels' array is empty."""
        data = {"channels": []}
        error = validate_channel_definition_schema(data)
        assert error == "No channels defined in the channel definition file"

    def test_channel_not_object(self):
        """Test validation fails when a channel is not an object."""
        data = {"channels": ["not an object"]}
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0 must be an object in the channel definition file"

    def test_missing_name(self, valid_channel_definition):
        """Test validation fails when 'name' is missing."""
        data = valid_channel_definition.copy()
        del data["channels"][0]["name"]
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0 is missing required field 'name' in the channel definition file"

    def test_name_not_string(self, valid_channel_definition):
        """Test validation fails when 'name' is not a string."""
        data = valid_channel_definition.copy()
        data["channels"][0]["name"] = 123
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: 'name' must be a string in the channel definition file"

    def test_name_too_long(self, valid_channel_definition):
        """Test validation fails when 'name' is too long."""
        data = valid_channel_definition.copy()
        data["channels"][0]["name"] = "x" * (MAX_CHANNEL_NAME_LENGTH + 1)
        error = validate_channel_definition_schema(data)
        assert (
            error
            == f"Channel at index 0: 'name' must be less than {MAX_CHANNEL_NAME_LENGTH} characters in the channel definition file"
        )

    def test_missing_channel_type(self, valid_channel_definition):
        """Test validation fails when 'channel_type' is missing."""
        data = valid_channel_definition.copy()
        del data["channels"][0]["channel_type"]
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0 is missing required field 'channel_type' in the channel definition file"

    def test_channel_type_not_string(self, valid_channel_definition):
        """Test validation fails when 'channel_type' is not a string."""
        data = valid_channel_definition.copy()
        data["channels"][0]["channel_type"] = 123
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: 'channel_type' must be a string in the channel definition file"

    def test_invalid_channel_type(self, valid_channel_definition):
        """Test validation fails when 'channel_type' is invalid."""
        data = valid_channel_definition.copy()
        data["channels"][0]["channel_type"] = "INVALID"
        error = validate_channel_definition_schema(data)
        assert (
            error
            == f"Channel at index 0: 'channel_type' must be one of: {', '.join(AVAILABLE_CHANNEL_TYPES)} in the channel definition file"
        )

    def test_missing_schemes(self, valid_channel_definition):
        """Test validation fails when 'schemes' is missing."""
        data = valid_channel_definition.copy()
        del data["channels"][0]["schemes"]
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0 is missing required field 'schemes' in the channel definition file"

    def test_schemes_not_array(self, valid_channel_definition):
        """Test validation fails when 'schemes' is not an array."""
        data = valid_channel_definition.copy()
        data["channels"][0]["schemes"] = "not an array"
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: 'schemes' must be an array in the channel definition file"

    def test_empty_schemes_array(self, valid_channel_definition):
        """Test validation fails when 'schemes' array is empty."""
        data = valid_channel_definition.copy()
        data["channels"][0]["schemes"] = []
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: 'schemes' must not be empty in the channel definition file"

    def test_scheme_not_string(self, valid_channel_definition):
        """Test validation fails when a scheme is not a string."""
        data = valid_channel_definition.copy()
        data["channels"][0]["schemes"] = [123]
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: scheme at index 0 must be a string in the channel definition file"

    def test_invalid_scheme(self, valid_channel_definition):
        """Test validation fails when a scheme is invalid."""
        data = valid_channel_definition.copy()
        data["channels"][0]["schemes"] = ["invalid"]
        error = validate_channel_definition_schema(data)
        assert (
            error
            == f"Channel at index 0: scheme at index 0 must be one of: {', '.join(AVAILABLE_SCHEMES)} in the channel definition file"
        )

    def test_missing_config(self, valid_channel_definition):
        """Test validation fails when 'config' is missing."""
        data = valid_channel_definition.copy()
        del data["channels"][0]["config"]
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0 is missing required field 'config' in the channel definition file"

    def test_config_not_object(self, valid_channel_definition):
        """Test validation fails when 'config' is not an object."""
        data = valid_channel_definition.copy()
        data["channels"][0]["config"] = "not an object"
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: 'config' must be an object in the channel definition file"

    def test_missing_send_url(self, valid_channel_definition):
        """Test validation fails when 'send_url' is missing from config."""
        data = valid_channel_definition.copy()
        del data["channels"][0]["config"]["send_url"]
        error = validate_channel_definition_schema(data)
        assert (
            error == "Channel at index 0: 'config' is missing required field 'send_url' in the channel definition file"
        )

    def test_send_url_not_string(self, valid_channel_definition):
        """Test validation fails when 'send_url' is not a string."""
        data = valid_channel_definition.copy()
        data["channels"][0]["config"]["send_url"] = 123
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: 'config.send_url' must be a string in the channel definition file"

    def test_send_url_empty(self, valid_channel_definition):
        """Test validation fails when 'send_url' is empty."""
        data = valid_channel_definition.copy()
        data["channels"][0]["config"]["send_url"] = ""
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: 'config.send_url' must not be empty in the channel definition file"

    def test_send_url_invalid_format(self, valid_channel_definition):
        """Test validation fails when 'send_url' is not a valid URL."""
        data = valid_channel_definition.copy()
        data["channels"][0]["config"]["send_url"] = "not-a-valid-url"
        error = validate_channel_definition_schema(data)
        assert (
            error
            == "Channel at index 0: 'config.send_url' must be a valid URL starting with http:// or https:// in the channel definition file"
        )

    def test_invalid_send_method(self, valid_channel_definition):
        """Test validation fails when 'send_method' is invalid."""
        data = valid_channel_definition.copy()
        data["channels"][0]["config"]["send_method"] = "INVALID"
        error = validate_channel_definition_schema(data)
        assert (
            error
            == f"Channel at index 0: 'config.send_method' must be one of: {', '.join(AVAILABLE_SEND_METHODS)} in the channel definition file"
        )

    def test_empty_send_template(self, valid_channel_definition):
        """Test validation fails when 'send_template' is empty."""
        data = valid_channel_definition.copy()
        data["channels"][0]["config"]["send_template"] = ""
        error = validate_channel_definition_schema(data)
        assert error == "Channel at index 0: 'config.send_template' must not be empty in the channel definition file"

    def test_invalid_content_type(self, valid_channel_definition):
        """Test validation fails when 'content_type' is invalid."""
        data = valid_channel_definition.copy()
        data["channels"][0]["config"]["content_type"] = "invalid/type"
        error = validate_channel_definition_schema(data)
        assert (
            error
            == f"Channel at index 0: 'config.content_type' must be one of: {', '.join(AVAILABLE_CONTENT_TYPES)} in the channel definition file"
        )

    def test_empty_receive_template(self, valid_channel_definition):
        """Test validation fails when 'receive_template' is empty."""
        data = valid_channel_definition.copy()
        data["channels"][0]["config"]["receive_template"] = ""
        error = validate_channel_definition_schema(data)
        assert (
            error == "Channel at index 0: 'config.receive_template' must not be empty in the channel definition file"
        )


class TestLoadChannelDefinition:
    """Tests for load_channel_definition function."""

    def test_load_valid_channel_definition(self, sample_definition_file):
        """Test loading a valid channel definition file."""
        data, error = load_channel_definition(sample_definition_file["valid_path"])
        assert error is None
        assert data is not None
        assert "channels" in data

    def test_load_empty_channel_definition(self, sample_definition_file):
        """Test loading an empty channel definition file."""
        data, error = load_channel_definition(sample_definition_file["empty_path"])
        assert error is not None
        assert "Empty definition file" in str(error)

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        data, error = load_channel_definition("nonexistent.yaml")
        assert error is not None
        assert data is None
