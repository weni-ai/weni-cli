from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.commands.channel_delete import ChannelDeleteHandler
from weni_cli.store import STORE_PROJECT_UUID_KEY

PROJECT_UUID = "123e4567-e89b-12d3-a456-426614174000"
CHANNEL_UUID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture
def mock_cli_client():
    with patch("weni_cli.commands.channel_delete.CLIClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_formatter():
    with patch("weni_cli.commands.channel_delete.Formatter") as mock_formatter_class:
        mock_formatter_instance = MagicMock()
        mock_formatter_class.return_value = mock_formatter_instance
        yield mock_formatter_instance


@pytest.fixture
def project_selected(mocker):
    return mocker.patch(
        "weni_cli.commands.channel_delete.Store.get",
        side_effect=lambda key, default=None: PROJECT_UUID if key == STORE_PROJECT_UUID_KEY else default,
    )


def test_delete_channel_with_yes_skips_confirmation(mock_cli_client, mock_formatter, project_selected, mocker):
    confirm = mocker.patch("weni_cli.commands.channel_delete.click.confirm")

    ChannelDeleteHandler().execute(channel_uuid=UUID(CHANNEL_UUID), yes=True)

    confirm.assert_not_called()
    mock_cli_client.delete_channel.assert_called_once_with(CHANNEL_UUID)
    mock_formatter.print_success_panel.assert_called_once_with(
        f"Channel deactivated successfully\nUUID: {CHANNEL_UUID}"
    )


def test_delete_channel_after_confirmation(mock_cli_client, mock_formatter, project_selected, mocker):
    mocker.patch("weni_cli.commands.channel_delete.click.confirm", return_value=True)

    ChannelDeleteHandler().execute(channel_uuid=CHANNEL_UUID)

    mock_cli_client.delete_channel.assert_called_once_with(CHANNEL_UUID)


def test_delete_channel_declined(mock_cli_client, mock_formatter, project_selected, mocker):
    mocker.patch("weni_cli.commands.channel_delete.click.confirm", return_value=False)

    ChannelDeleteHandler().execute(channel_uuid=CHANNEL_UUID)

    mock_cli_client.delete_channel.assert_not_called()
    mock_formatter.print_warning_panel.assert_called_once_with("Channel deletion cancelled")


def test_delete_channel_requires_uuid(mock_cli_client, mock_formatter):
    ChannelDeleteHandler().execute(yes=True)

    mock_formatter.print_error_panel.assert_called_once_with("Channel UUID is required")
    mock_cli_client.delete_channel.assert_not_called()


def test_delete_channel_without_project(mock_cli_client, mock_formatter, mocker):
    mocker.patch("weni_cli.commands.channel_delete.Store.get", return_value=None)

    ChannelDeleteHandler().execute(channel_uuid=CHANNEL_UUID, yes=True)

    mock_formatter.print_error_panel.assert_called_once_with("No project selected, please select a project first")
    mock_cli_client.delete_channel.assert_not_called()


def test_delete_channel_command_prompts_and_aborts(mock_cli_client, project_selected):
    result = CliRunner().invoke(cli, ["channel", "delete", CHANNEL_UUID], input="n\n")

    assert result.exit_code == 0
    assert "Deactivate channel" in result.output
    mock_cli_client.delete_channel.assert_not_called()


def test_delete_channel_command_passes_yes(mocker):
    handler = mocker.patch("weni_cli.commands.channel_delete.ChannelDeleteHandler.execute")

    result = CliRunner().invoke(cli, ["channel", "delete", CHANNEL_UUID, "--yes"])

    assert result.exit_code == 0
    handler.assert_called_once_with(channel_uuid=UUID(CHANNEL_UUID), yes=True)


def test_delete_channel_command_reports_errors(mocker):
    mocker.patch(
        "weni_cli.commands.channel_delete.ChannelDeleteHandler.execute",
        side_effect=Exception("Failed to delete channel: Channel not found"),
    )

    result = CliRunner().invoke(cli, ["channel", "delete", CHANNEL_UUID, "--yes"])

    assert result.exit_code == 0
    assert "Error: Failed to delete channel: Channel not found" in result.output
