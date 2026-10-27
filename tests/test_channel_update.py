from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.commands.channel_update import ChannelUpdateHandler
from weni_cli.store import STORE_PROJECT_UUID_KEY

PROJECT_UUID = "123e4567-e89b-12d3-a456-426614174000"
CHANNEL_UUID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture
def mock_cli_client():
    with patch("weni_cli.commands.channel_update.CLIClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_formatter():
    with patch("weni_cli.commands.channel_update.Formatter") as mock_formatter_class:
        mock_formatter_instance = MagicMock()
        mock_formatter_class.return_value = mock_formatter_instance
        yield mock_formatter_instance


@pytest.fixture
def project_selected(mocker):
    return mocker.patch(
        "weni_cli.commands.channel_update.Store.get",
        side_effect=lambda key, default=None: PROJECT_UUID if key == STORE_PROJECT_UUID_KEY else default,
    )


def test_update_channel_name_and_config_file(mock_cli_client, mock_formatter, project_selected, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("base_url: https://example.com\nverify_ssl: false\n")
    mock_cli_client.update_channel.return_value = {"uuid": CHANNEL_UUID, "name": "Renamed"}

    ChannelUpdateHandler().execute(channel_uuid=UUID(CHANNEL_UUID), name="Renamed", config_file=str(config_file))

    mock_cli_client.update_channel.assert_called_once_with(
        CHANNEL_UUID,
        name="Renamed",
        address=None,
        config={"base_url": "https://example.com", "verify_ssl": False},
    )
    mock_formatter.print_success_panel.assert_called_once_with(
        f"Channel updated successfully\nName: Renamed\nUUID: {CHANNEL_UUID}"
    )


def test_update_channel_address_only(mock_cli_client, mock_formatter, project_selected):
    mock_cli_client.update_channel.return_value = {}

    ChannelUpdateHandler().execute(channel_uuid=CHANNEL_UUID, address="+5511999999999")

    mock_cli_client.update_channel.assert_called_once_with(
        CHANNEL_UUID, name=None, address="+5511999999999", config=None
    )
    mock_formatter.print_success_panel.assert_called_once_with("Channel updated successfully")


@pytest.mark.parametrize("response", [None, {"uuid": None, "name": ""}])
def test_update_channel_response_without_details(mock_cli_client, mock_formatter, project_selected, response):
    mock_cli_client.update_channel.return_value = response

    ChannelUpdateHandler().execute(channel_uuid=CHANNEL_UUID, name="Renamed")

    mock_formatter.print_success_panel.assert_called_once_with("Channel updated successfully")


def test_update_channel_response_with_uuid_only(mock_cli_client, mock_formatter, project_selected):
    mock_cli_client.update_channel.return_value = {"uuid": CHANNEL_UUID}

    ChannelUpdateHandler().execute(channel_uuid=CHANNEL_UUID, name="Renamed")

    mock_formatter.print_success_panel.assert_called_once_with(
        f"Channel updated successfully\nUUID: {CHANNEL_UUID}"
    )


def test_update_channel_requires_uuid(mock_cli_client, mock_formatter):
    ChannelUpdateHandler().execute(name="Renamed")

    mock_formatter.print_error_panel.assert_called_once_with("Channel UUID is required")
    mock_cli_client.update_channel.assert_not_called()


def test_update_channel_requires_a_field(mock_cli_client, mock_formatter, project_selected):
    ChannelUpdateHandler().execute(channel_uuid=CHANNEL_UUID)

    mock_formatter.print_error_panel.assert_called_once_with(
        "Provide at least one of --name, --address or --config-file"
    )
    mock_cli_client.update_channel.assert_not_called()


@pytest.mark.parametrize("content", ["- not\n- a mapping\n", ""])
def test_update_channel_rejects_invalid_config_file(mock_cli_client, mock_formatter, project_selected, tmp_path, content):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(content)

    ChannelUpdateHandler().execute(channel_uuid=CHANNEL_UUID, config_file=str(config_file))

    mock_formatter.print_error_panel.assert_called_once_with("Config file must contain a non-empty key/value mapping")
    mock_cli_client.update_channel.assert_not_called()


def test_update_channel_reports_unreadable_config_file(mock_cli_client, mock_formatter, project_selected, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: [unclosed\n")

    ChannelUpdateHandler().execute(channel_uuid=CHANNEL_UUID, config_file=str(config_file))

    message = mock_formatter.print_error_panel.call_args[0][0]
    assert message.startswith("Could not read config file:")
    mock_cli_client.update_channel.assert_not_called()


def test_update_channel_without_project(mock_cli_client, mock_formatter, mocker):
    mocker.patch("weni_cli.commands.channel_update.Store.get", return_value=None)

    ChannelUpdateHandler().execute(channel_uuid=CHANNEL_UUID, name="Renamed")

    mock_formatter.print_error_panel.assert_called_once_with("No project selected, please select a project first")
    mock_cli_client.update_channel.assert_not_called()


def test_update_channel_command_passes_options(mocker, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("base_url: https://example.com\n")
    handler = mocker.patch("weni_cli.commands.channel_update.ChannelUpdateHandler.execute")

    result = CliRunner().invoke(
        cli,
        ["channel", "update", CHANNEL_UUID, "--name", "Renamed", "-a", "123", "--config-file", str(config_file)],
    )

    assert result.exit_code == 0
    handler.assert_called_once_with(
        channel_uuid=UUID(CHANNEL_UUID), name="Renamed", address="123", config_file=str(config_file)
    )


def test_update_channel_command_reports_errors(mocker):
    mocker.patch(
        "weni_cli.commands.channel_update.ChannelUpdateHandler.execute",
        side_effect=Exception("Failed to update channel: Invalid"),
    )

    result = CliRunner().invoke(cli, ["channel", "update", CHANNEL_UUID, "--name", "Renamed"])

    assert result.exit_code == 0
    assert "Error: Failed to update channel: Invalid" in result.output
