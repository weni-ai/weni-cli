import json

import pytest
from click.testing import CliRunner

from weni_cli.validators.ticketer_definition import (
    AVAILABLE_TICKETER_TYPES,
    MAX_TICKETER_NAME_LENGTH,
    load_ticketer_definition,
    validate_ticketer_definition_schema,
)


def _clone_definition(valid_ticketer_definition):
    data = valid_ticketer_definition.copy()
    data["ticketers"] = [dict(data["ticketers"][0])]
    data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
    return data


def _custom_refresh_object():
    return {
        "when": {
            "match": "any",
            "status_codes": [401, 403],
            "body_contains": ["INVALID_SESSION_ID", "token_expired"],
            "expired": True,
        },
        "method": "POST",
        "url": "https://example.my.salesforce.com/services/oauth2/token",
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "body": "grant_type=password&client_id=id&client_secret=secret&username=user&password=pass",
        "token_field": "access_token",
        "expires_in_field": "expires_in",
        "expires_in_default": 7200,
    }


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
            error == "Ticketer at index 0: 'config.webhook_secret' is required unless "
            "'config.skip_webhook_hmac' is set to true, 1 or yes in the ticketer definition file"
        )

    def test_config_value_not_string(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
        data["ticketers"][0]["config"]["api_token"] = 123
        error = validate_ticketer_definition_schema(data)
        assert error == "Ticketer at index 0: 'config.api_token' must be a string in the ticketer definition file"

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

    def test_valid_ticketer_definition_with_equivalent_templates(self, valid_ticketer_definition):
        data = valid_ticketer_definition.copy()
        data["ticketers"] = [dict(data["ticketers"][0])]
        data["ticketers"][0]["config"] = dict(data["ticketers"][0]["config"])
        data["ticketers"][0]["config"].update(
            {
                "open_template": '{"ticket_id":{{json .ticket_id}},"contact":{{json .contact}},'
                '"body":{{json .body}},"topic":{{json .topic}},"assignee":{{json .assignee}},'
                '"metadata":{{json .metadata}},"opened_at":{{json .opened_at}}}',
                "open_response_template": '{"external_id":{{json .external_id}},'
                '"status":{{json .status}},"created_at":{{json .created_at}}}',
                "forward_template": '{"ticket_id":{{json .ticket_id}},"external_id":{{json .external_id}},'
                '"message_id":{{json .message_id}},"direction":{{json .direction}},'
                '"sender":{{json .sender}},"text":{{json .text}},"attachments":{{json .attachments}},'
                '"metadata":{{json .metadata}},"sent_at":{{json .sent_at}}}',
                "forward_response_template": '{"message_external_id":{{json .message_external_id}},'
                '"status":{{json .status}}}',
                "close_template": '{"ticket_id":{{json .ticket_id}},"external_id":{{json .external_id}},'
                '"closed_by":{{json .closed_by}},"reason":{{json .reason}},'
                '"metadata":{{json .metadata}},"closed_at":{{json .closed_at}}}',
                "close_response_template": '{"status":{{json .status}}}',
                "history_mode": "batch",
                "history_batch_size": "50",
                "route_history_message": "/v1/tickets/{external_id}/messages",
                "history_template": '{"ticket_id":{{json .ticket_id}},"external_id":{{json .external_id}},'
                '"contact":{{json .contact}},"messages":{{json .messages}},"metadata":{{json .metadata}}}',
                "history_response_template": '{"status":{{json .status}},'
                '"messages_received":{{json .messages_received}}}',
                "messages_template": '{"external_id":{{json .external_id}},'
                '"message_external_id":{{json .message_external_id}},"direction":{{json .direction}},'
                '"sender":{{json .sender}},"text":{{json .text}},"attachments":{{json .attachments}},'
                '"metadata":{{json .metadata}},"sent_at":{{json .sent_at}}}',
                "messages_response_template": '{"status":{{json .status}},'
                '"ticket_uuid":{{json .ticket_uuid}},"message_uuid":{{json .message_uuid}}}',
                "tickets_close_template": '{"external_id":{{json .external_id}},'
                '"closed_by":{{json .closed_by}},"reason":{{json .reason}},'
                '"metadata":{{json .metadata}},"closed_at":{{json .closed_at}}}',
                "tickets_close_response_template": '{"status":{{json .status}},'
                '"ticket_uuid":{{json .ticket_uuid}}}',
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error is None


class TestTokenRefreshConfig:
    """OAuth2 token refresh config validation and string serialization."""

    def test_disabled_by_default_without_refresh_fields(self, valid_ticketer_definition):
        error = validate_ticketer_definition_schema(valid_ticketer_definition)
        assert error is None
        assert "token_refresh_enabled" not in valid_ticketer_definition["ticketers"][0]["config"]

    def test_enabled_custom_nested_object_serializes_compact_json_string(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        refresh_object = _custom_refresh_object()
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "custom",
                "expires_in": "1774132800",
                "token_refresh_config": refresh_object,
            }
        )

        error = validate_ticketer_definition_schema(data)
        assert error is None

        serialized = data["ticketers"][0]["config"]["token_refresh_config"]
        assert isinstance(serialized, str)
        assert "\n" not in serialized
        assert json.loads(serialized) == refresh_object

    def test_enabled_custom_json_string_is_normalized(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        refresh_object = _custom_refresh_object()
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "TRUE",
                "token_refresh_type": "custom",
                "token_refresh_config": json.dumps(refresh_object, indent=2),
            }
        )

        error = validate_ticketer_definition_schema(data)
        assert error is None
        serialized = data["ticketers"][0]["config"]["token_refresh_config"]
        assert isinstance(serialized, str)
        assert "\n" not in serialized
        assert json.loads(serialized) == refresh_object

    def test_enabled_refresh_type_requires_refresh_token_and_strips_body(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "1",
                "token_refresh_type": "refresh",
                "refresh_token": "rt-secret",
                "client_id": "cid",
                "client_secret": "csecret",
                "token_refresh_config": {
                    "url": "https://host/oauth/token",
                    "body": "should-be-ignored",
                },
            }
        )

        error = validate_ticketer_definition_schema(data)
        assert error is None
        parsed = json.loads(data["ticketers"][0]["config"]["token_refresh_config"])
        assert "body" not in parsed
        assert parsed["url"] == "https://host/oauth/token"
        assert parsed["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    def test_enabled_without_type_fails(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"]["token_refresh_enabled"] = "yes"
        data["ticketers"][0]["config"]["token_refresh_config"] = json.dumps({"url": "https://host/token", "body": "x"})
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.token_refresh_type' is required when "
            "token refresh is enabled and must be 'custom' or 'refresh' in the ticketer definition file"
        )

    def test_enabled_invalid_type_fails(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "authorization_code",
                "token_refresh_config": json.dumps({"url": "https://host/token", "body": "x"}),
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.token_refresh_type' is required when "
            "token refresh is enabled and must be 'custom' or 'refresh' in the ticketer definition file"
        )

    def test_enabled_invalid_json_fails(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "custom",
                "token_refresh_config": "{not-json",
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.token_refresh_config' must be valid JSON " "in the ticketer definition file"
        )

    def test_enabled_missing_url_fails(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "custom",
                "token_refresh_config": {"body": "grant_type=password"},
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.token_refresh_config.url' is required "
            "when token refresh is enabled in the ticketer definition file"
        )

    def test_when_match_must_be_any(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "custom",
                "token_refresh_config": {
                    "url": "https://host/token",
                    "body": "x",
                    "when": {"match": "all"},
                },
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.token_refresh_config.when.match' must be 'any' "
            "in the ticketer definition file"
        )

    def test_custom_missing_body_fails(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "custom",
                "token_refresh_config": {"url": "https://host/token"},
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.token_refresh_config.body' is required "
            "when token_refresh_type is 'custom' in the ticketer definition file"
        )

    def test_refresh_missing_refresh_token_fails(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "refresh",
                "token_refresh_config": {"url": "https://host/token"},
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.refresh_token' is required when "
            "token_refresh_type is 'refresh' in the ticketer definition file"
        )

    def test_expires_in_must_be_int64(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "custom",
                "expires_in": "not-a-timestamp",
                "token_refresh_config": _custom_refresh_object(),
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.expires_in' must be a decimal int64 unix timestamp "
            "in the ticketer definition file"
        )

    def test_enabled_missing_token_refresh_config_fails(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"].update(
            {
                "token_refresh_enabled": "true",
                "token_refresh_type": "custom",
            }
        )
        error = validate_ticketer_definition_schema(data)
        assert error == (
            "Ticketer at index 0: 'config.token_refresh_config' is required "
            "when token refresh is enabled in the ticketer definition file"
        )

    def test_enabled_false_does_not_require_refresh_fields(self, valid_ticketer_definition):
        data = _clone_definition(valid_ticketer_definition)
        data["ticketers"][0]["config"]["token_refresh_enabled"] = "false"
        error = validate_ticketer_definition_schema(data)
        assert error is None


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
