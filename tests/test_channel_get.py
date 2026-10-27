import json
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.commands.channel_get import ChannelGetHandler, mask_secrets
from weni_cli.store import STORE_PROJECT_UUID_KEY

PROJECT_UUID = "123e4567-e89b-12d3-a456-426614174000"
CHANNEL_UUID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture
def mock_cli_client():
    with patch("weni_cli.commands.channel_get.CLIClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_formatter():
    with patch("weni_cli.commands.channel_get.Formatter") as mock_formatter_class:
        mock_formatter_instance = MagicMock()
        mock_formatter_class.return_value = mock_formatter_instance
        yield mock_formatter_instance


@pytest.fixture
def project_selected(mocker):
    return mocker.patch(
        "weni_cli.commands.channel_get.Store.get",
        side_effect=lambda key, default=None: PROJECT_UUID if key == STORE_PROJECT_UUID_KEY else default,
    )


def _channel(config):
    return {
        "uuid": CHANNEL_UUID,
        "name": "WhatsApp",
        "channel_type": "WAC",
        "address": "123456",
        "is_active": True,
        "org": PROJECT_UUID,
        "config": config,
    }


def test_mask_secrets_masks_nested_secret_keys():
    config = {
        "auth_token": "abc",
        "wa_number": "5561999999999",
        "nested": {"api_key": "xyz", "base_url": "https://example.com"},
        "items": [{"password": "p"}],
    }

    assert mask_secrets(config) == {
        "auth_token": "****",
        "wa_number": "5561999999999",
        "nested": {"api_key": "****", "base_url": "https://example.com"},
        "items": [{"password": "****"}],
    }


def test_get_channel_masks_secrets_by_default(mock_cli_client, mock_formatter, project_selected):
    mock_cli_client.get_channel.return_value = _channel({"auth_token": "abc", "wa_number": "5561"})

    ChannelGetHandler().execute(channel_uuid=UUID(CHANNEL_UUID))

    mock_cli_client.get_channel.assert_called_once_with(CHANNEL_UUID)
    output = mock_formatter.print_success_panel.call_args[0][0]
    assert f"UUID: {CHANNEL_UUID}" in output
    assert "Type: WAC" in output
    assert "Active: yes" in output
    assert f"Project: {PROJECT_UUID}" in output
    assert json.dumps({"auth_token": "****", "wa_number": "5561"}, indent=2) in output
    assert "abc" not in output


def test_get_channel_show_secrets(mock_cli_client, mock_formatter, project_selected):
    mock_cli_client.get_channel.return_value = _channel({"auth_token": "abc"})

    ChannelGetHandler().execute(channel_uuid=CHANNEL_UUID, show_secrets=True)

    output = mock_formatter.print_success_panel.call_args[0][0]
    assert '"auth_token": "abc"' in output


def test_get_channel_without_config(mock_cli_client, mock_formatter, project_selected):
    channel = _channel(None)
    channel["address"] = None
    channel["is_active"] = False
    mock_cli_client.get_channel.return_value = channel

    ChannelGetHandler().execute(channel_uuid=CHANNEL_UUID)

    output = mock_formatter.print_success_panel.call_args[0][0]
    assert "Address: \n" in output
    assert "Active: no" in output
    assert output.endswith("Config:\n{}")


def test_get_channel_requires_uuid(mock_cli_client, mock_formatter):
    ChannelGetHandler().execute()

    mock_formatter.print_error_panel.assert_called_once_with("Channel UUID is required")
    mock_cli_client.get_channel.assert_not_called()


def test_get_channel_without_project(mock_cli_client, mock_formatter, mocker):
    mocker.patch("weni_cli.commands.channel_get.Store.get", return_value=None)

    ChannelGetHandler().execute(channel_uuid=CHANNEL_UUID)

    mock_formatter.print_error_panel.assert_called_once_with("No project selected, please select a project first")
    mock_cli_client.get_channel.assert_not_called()


def test_get_channel_command_passes_options(mocker):
    handler = mocker.patch("weni_cli.commands.channel_get.ChannelGetHandler.execute")

    result = CliRunner().invoke(cli, ["channel", "get", CHANNEL_UUID, "--show-secrets"])

    assert result.exit_code == 0
    handler.assert_called_once_with(channel_uuid=UUID(CHANNEL_UUID), show_secrets=True)


def test_get_channel_command_reports_errors(mocker):
    mocker.patch(
        "weni_cli.commands.channel_get.ChannelGetHandler.execute",
        side_effect=Exception("Failed to get channel: Channel not found"),
    )

    result = CliRunner().invoke(cli, ["channel", "get", CHANNEL_UUID])

    assert result.exit_code == 0
    assert "Error: Failed to get channel: Channel not found" in result.output


def test_get_channel_command_rejects_invalid_uuid(mocker):
    handler = mocker.patch("weni_cli.commands.channel_get.ChannelGetHandler.execute")

    result = CliRunner().invoke(cli, ["channel", "get", "not-a-uuid"])

    assert result.exit_code != 0
    handler.assert_not_called()
