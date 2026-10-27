from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.commands.channel_list import ChannelListHandler
from weni_cli.store import STORE_PROJECT_UUID_KEY

PROJECT_UUID = "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def mock_cli_client():
    with patch("weni_cli.commands.channel_list.CLIClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_formatter():
    with patch("weni_cli.commands.channel_list.Formatter") as mock_formatter_class:
        mock_formatter_instance = MagicMock()
        mock_formatter_class.return_value = mock_formatter_instance
        yield mock_formatter_instance


@pytest.fixture
def mock_console():
    with patch("weni_cli.commands.channel_list.Console") as mock_console_class:
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        yield mock_console


@pytest.fixture
def project_selected(mocker):
    return mocker.patch(
        "weni_cli.commands.channel_list.Store.get",
        side_effect=lambda key, default=None: PROJECT_UUID if key == STORE_PROJECT_UUID_KEY else default,
    )


def test_list_channels_prints_table(mock_cli_client, mock_formatter, mock_console, project_selected):
    mock_cli_client.list_channels.return_value = [
        {
            "uuid": "channel-1",
            "name": "WhatsApp",
            "channel_type": "WAC",
            "address": "123456",
            "is_active": True,
        },
        {"uuid": "channel-2", "name": "Web Chat", "channel_type": "WWC", "address": None, "is_active": False},
    ]

    ChannelListHandler().execute(channel_type="WAC", exclude_wpp_demo=True)

    mock_cli_client.list_channels.assert_called_once_with(channel_type="WAC", exclude_wpp_demo=True)
    mock_console.print.assert_called_once()
    table = mock_console.print.call_args[0][0]
    assert table.row_count == 2
    assert [column.header for column in table.columns] == ["UUID", "Name", "Type", "Address", "Active"]
    assert list(table.columns[0].cells) == ["channel-1", "channel-2"]
    assert list(table.columns[3].cells) == ["123456", ""]
    assert list(table.columns[4].cells) == ["yes", "no"]
    mock_formatter.print_error_panel.assert_not_called()


def test_list_channels_empty(mock_cli_client, mock_formatter, mock_console, project_selected):
    mock_cli_client.list_channels.return_value = []

    ChannelListHandler().execute()

    mock_formatter.print_warning_panel.assert_called_once_with("No channels found for this project")
    mock_console.print.assert_not_called()


def test_list_channels_without_project(mock_cli_client, mock_formatter, mocker):
    mocker.patch("weni_cli.commands.channel_list.Store.get", return_value=None)

    ChannelListHandler().execute()

    mock_formatter.print_error_panel.assert_called_once_with("No project selected, please select a project first")
    mock_cli_client.list_channels.assert_not_called()


def test_list_channels_command_passes_options(mocker):
    handler = mocker.patch("weni_cli.commands.channel_list.ChannelListHandler.execute")

    result = CliRunner().invoke(cli, ["channel", "list", "--type", "WAC", "--exclude-wpp-demo"])

    assert result.exit_code == 0
    handler.assert_called_once_with(channel_type="WAC", exclude_wpp_demo=True)


def test_list_channels_command_reports_errors(mocker):
    mocker.patch(
        "weni_cli.commands.channel_list.ChannelListHandler.execute",
        side_effect=Exception("Failed to list channels: Forbidden"),
    )

    result = CliRunner().invoke(cli, ["channel", "list"])

    assert result.exit_code == 0
    assert "Error: Failed to list channels: Forbidden" in result.output
