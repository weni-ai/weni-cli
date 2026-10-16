from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.clients.cli_client import RequestError
from weni_cli.commands.ticketer_delete import TicketerDeleteHandler
from weni_cli.commands.ticketer_get import TicketerGetHandler
from weni_cli.commands.ticketer_list import TicketerListHandler
from weni_cli.commands.ticketer_update import TicketerUpdateHandler

PROJECT_UUID = "project-uuid"
TICKETER_UUID = "ticketer-uuid"

DEFINITION_YAML = """
ticketers:
  - name: org support
    ticketer_type: generic
    config:
      base_url: https://example.com
      api_token: test-api-token
      webhook_secret: test-webhook-secret
"""

DEFINITION_WITH_PROJECT_YAML = """
ticketers:
  - name: org support
    ticketer_type: generic
    config:
      base_url: https://example.com
      api_token: test-api-token
      webhook_secret: test-webhook-secret
      project_uuid: kept-uuid
"""

INVALID_DEFINITION_YAML = """
ticketers:
  - name: org support
"""


def _invoke(args):
    runner = CliRunner()
    with runner.isolated_filesystem():
        return runner.invoke(cli, args, terminal_width=80)


def _write(name, content):
    with open(name, "w") as definition_file:
        definition_file.write(content)


def test_list_ticketers_requires_project(mocker):
    mocker.patch("weni_cli.commands.ticketer_list.Store.get", return_value="")
    result = _invoke(["ticketer", "list"])

    assert result.exit_code == 0
    assert "No project selected, please select a project first" in result.output


def test_list_ticketers_empty(mocker):
    mocker.patch("weni_cli.commands.ticketer_list.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_list.CLIClient")
    client.return_value.list_ticketers.return_value = {}

    result = _invoke(["ticketer", "list"])

    assert result.exit_code == 0
    assert "No ticketers found" in result.output


def test_list_ticketers_prints_table(mocker):
    mocker.patch("weni_cli.commands.ticketer_list.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_list.CLIClient")
    client.return_value.list_ticketers.return_value = {
        "results": [
            {
                "uuid": TICKETER_UUID,
                "name": "org support",
                "ticketer_type": "generic",
                "created_on": "2024-01-01T00:00:00Z",
            },
            {"type": "generic"},
            {},
        ]
    }

    result = _invoke(["ticketer", "list"])

    assert result.exit_code == 0
    assert "org support" in result.output
    assert TICKETER_UUID in result.output
    assert "generic" in result.output


def test_list_ticketers_empty_results_array(mocker):
    mocker.patch("weni_cli.commands.ticketer_list.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_list.CLIClient")
    client.return_value.list_ticketers.return_value = {"results": []}

    TicketerListHandler().execute()

    client.return_value.list_ticketers.assert_called_once_with(PROJECT_UUID)


def test_list_ticketers_reports_request_error(mocker):
    mocker.patch("weni_cli.commands.ticketer_list.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_list.CLIClient")
    client.return_value.list_ticketers.side_effect = RequestError("backend down", status_code=500)

    result = _invoke(["ticketer", "list"])

    assert result.exit_code == 0
    assert "Error: backend down" in result.output


def test_get_ticketer_requires_uuid(capsys):
    TicketerGetHandler().execute(ticketer_uuid="")
    assert "Ticketer UUID is required" in capsys.readouterr().out


def test_get_ticketer_requires_project(mocker):
    mocker.patch("weni_cli.commands.ticketer_get.Store.get", return_value="")
    result = _invoke(["ticketer", "get", TICKETER_UUID])

    assert result.exit_code == 0
    assert "No project selected, please select a project first" in result.output


def test_get_ticketer_prints_details(mocker):
    mocker.patch("weni_cli.commands.ticketer_get.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_get.CLIClient")
    client.return_value.get_ticketer.return_value = {
        "name": "org support",
        "uuid": TICKETER_UUID,
        "ticketer_type": "generic",
        "created_on": "2024-01-01T00:00:00Z",
        "modified_on": "2024-01-02T00:00:00Z",
        "config": {"base_url": "https://example.com"},
    }

    result = _invoke(["ticketer", "get", TICKETER_UUID])

    assert result.exit_code == 0
    assert "org support" in result.output
    assert TICKETER_UUID in result.output
    assert "https://example.com" in result.output


def test_get_ticketer_falls_back_when_fields_are_missing(mocker):
    mocker.patch("weni_cli.commands.ticketer_get.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_get.CLIClient")
    client.return_value.get_ticketer.return_value = {"type": "generic", "config": None}

    result = _invoke(["ticketer", "get", TICKETER_UUID])

    assert result.exit_code == 0
    assert "Type: generic" in result.output
    assert f"UUID: {TICKETER_UUID}" in result.output


def test_get_ticketer_accepts_non_dict_response(mocker):
    mocker.patch("weni_cli.commands.ticketer_get.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_get.CLIClient")
    client.return_value.get_ticketer.return_value = ["unexpected"]

    result = _invoke(["ticketer", "get", TICKETER_UUID])

    assert result.exit_code == 0
    assert f"UUID: {TICKETER_UUID}" in result.output


def test_get_ticketer_reports_request_error(mocker):
    mocker.patch("weni_cli.commands.ticketer_get.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_get.CLIClient")
    client.return_value.get_ticketer.side_effect = RequestError("missing", status_code=404)

    result = _invoke(["ticketer", "get", TICKETER_UUID])

    assert result.exit_code == 0
    assert "Error: missing" in result.output


def test_update_ticketer_requires_uuid(mocker):
    mocker.patch("weni_cli.commands.ticketer_update.Store.get", return_value=PROJECT_UUID)
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write("ticketer.yaml", DEFINITION_YAML)
        result = runner.invoke(cli, ["ticketer", "update", "", "ticketer.yaml"], terminal_width=80)

    assert result.exit_code == 0
    assert "Ticketer UUID is required" in result.output


def test_update_ticketer_requires_definition_path(capsys):
    TicketerUpdateHandler().execute(ticketer_uuid=TICKETER_UUID, ticketer_definition="")
    assert "Ticketer definition path is required" in capsys.readouterr().out


def test_update_ticketer_requires_project(mocker):
    mocker.patch("weni_cli.commands.ticketer_update.Store.get", return_value="")
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write("ticketer.yaml", DEFINITION_YAML)
        result = runner.invoke(cli, ["ticketer", "update", TICKETER_UUID, "ticketer.yaml"], terminal_width=80)

    assert result.exit_code == 0
    assert "No project selected, please select a project first" in result.output


def test_update_ticketer_reports_load_error(mocker):
    mocker.patch("weni_cli.commands.ticketer_update.Store.get", return_value=PROJECT_UUID)
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write("ticketer.yaml", "")
        result = runner.invoke(cli, ["ticketer", "update", TICKETER_UUID, "ticketer.yaml"], terminal_width=80)

    assert result.exit_code == 0
    assert "Empty definition file" in result.output


def test_update_ticketer_reports_schema_error(mocker):
    mocker.patch("weni_cli.commands.ticketer_update.Store.get", return_value=PROJECT_UUID)
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write("ticketer.yaml", INVALID_DEFINITION_YAML)
        result = runner.invoke(cli, ["ticketer", "update", TICKETER_UUID, "ticketer.yaml"], terminal_width=80)

    assert result.exit_code == 0
    assert "ticketer_type" in result.output


def test_update_ticketer_fills_project_uuid(mocker):
    mocker.patch("weni_cli.commands.ticketer_update.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_update.CLIClient")
    client.return_value.update_ticketer.return_value = {"name": "org support", "uuid": TICKETER_UUID}
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write("ticketer.yaml", DEFINITION_YAML)
        result = runner.invoke(cli, ["ticketer", "update", TICKETER_UUID, "ticketer.yaml"], terminal_width=80)

    sent = client.return_value.update_ticketer.call_args.args[2]
    assert sent["ticketers"][0]["config"]["project_uuid"] == PROJECT_UUID
    assert result.exit_code == 0
    assert "org support" in result.output
    assert TICKETER_UUID in result.output


def test_update_ticketer_keeps_existing_project_uuid(mocker):
    mocker.patch("weni_cli.commands.ticketer_update.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_update.CLIClient")
    client.return_value.update_ticketer.return_value = {}
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write("ticketer.yaml", DEFINITION_WITH_PROJECT_YAML)
        result = runner.invoke(cli, ["ticketer", "update", TICKETER_UUID, "ticketer.yaml"], terminal_width=80)

    sent = client.return_value.update_ticketer.call_args.args[2]
    assert sent["ticketers"][0]["config"]["project_uuid"] == "kept-uuid"
    assert result.exit_code == 0
    assert "Ticketer updated successfully" in result.output


def test_update_ticketer_accepts_non_dict_response(mocker):
    mocker.patch("weni_cli.commands.ticketer_update.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_update.CLIClient")
    client.return_value.update_ticketer.return_value = ["unexpected"]
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write("ticketer.yaml", DEFINITION_WITH_PROJECT_YAML)
        result = runner.invoke(cli, ["ticketer", "update", TICKETER_UUID, "ticketer.yaml"], terminal_width=80)

    assert result.exit_code == 0
    assert "Ticketer updated successfully" in result.output


def test_update_ticketer_reports_request_error(mocker):
    mocker.patch("weni_cli.commands.ticketer_update.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_update.CLIClient")
    client.return_value.update_ticketer.side_effect = RequestError("rejected", status_code=400)
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write("ticketer.yaml", DEFINITION_YAML)
        result = runner.invoke(cli, ["ticketer", "update", TICKETER_UUID, "ticketer.yaml"], terminal_width=80)

    assert result.exit_code == 0
    assert "Error: rejected" in result.output


def test_update_ticketer_ensure_project_uuid_branches():
    handler = TicketerUpdateHandler()

    untouched = {}
    handler._ensure_project_uuid(untouched, PROJECT_UUID)
    assert untouched == {}

    empty = {"ticketers": []}
    handler._ensure_project_uuid(empty, PROJECT_UUID)
    assert empty == {"ticketers": []}

    missing_config = {"ticketers": [{}]}
    handler._ensure_project_uuid(missing_config, PROJECT_UUID)
    assert missing_config["ticketers"][0]["config"]["project_uuid"] == PROJECT_UUID

    blank = {"ticketers": [{"config": {"project_uuid": "  "}}]}
    handler._ensure_project_uuid(blank, PROJECT_UUID)
    assert blank["ticketers"][0]["config"]["project_uuid"] == PROJECT_UUID


def test_delete_ticketer_requires_uuid(capsys):
    TicketerDeleteHandler().execute(ticketer_uuid="")
    assert "Ticketer UUID is required" in capsys.readouterr().out


def test_delete_ticketer_requires_project(mocker):
    mocker.patch("weni_cli.commands.ticketer_delete.Store.get", return_value="")
    result = _invoke(["ticketer", "delete", TICKETER_UUID, "--yes"])

    assert result.exit_code == 0
    assert "No project selected, please select a project first" in result.output


def test_delete_ticketer_can_be_cancelled(mocker):
    mocker.patch("weni_cli.commands.ticketer_delete.Store.get", return_value=PROJECT_UUID)
    confirm = mocker.patch("weni_cli.commands.ticketer_delete.click.confirm", return_value=False)
    client = mocker.patch("weni_cli.commands.ticketer_delete.CLIClient")

    result = _invoke(["ticketer", "delete", TICKETER_UUID])

    confirm.assert_called_once()
    client.return_value.delete_ticketer.assert_not_called()
    assert result.exit_code == 0
    assert "Delete cancelled" in result.output


def test_delete_ticketer_confirms_before_deleting(mocker):
    mocker.patch("weni_cli.commands.ticketer_delete.Store.get", return_value=PROJECT_UUID)
    mocker.patch("weni_cli.commands.ticketer_delete.click.confirm", return_value=True)
    client = mocker.patch("weni_cli.commands.ticketer_delete.CLIClient")

    result = _invoke(["ticketer", "delete", TICKETER_UUID])

    client.return_value.delete_ticketer.assert_called_once_with(PROJECT_UUID, TICKETER_UUID)
    assert result.exit_code == 0
    assert "Ticketer deleted successfully" in result.output
    assert TICKETER_UUID in result.output


def test_delete_ticketer_skips_prompt_with_yes(mocker):
    mocker.patch("weni_cli.commands.ticketer_delete.Store.get", return_value=PROJECT_UUID)
    confirm = mocker.patch("weni_cli.commands.ticketer_delete.click.confirm", return_value=False)
    client = mocker.patch("weni_cli.commands.ticketer_delete.CLIClient")

    result = _invoke(["ticketer", "delete", TICKETER_UUID, "--yes"])

    confirm.assert_not_called()
    client.return_value.delete_ticketer.assert_called_once_with(PROJECT_UUID, TICKETER_UUID)
    assert result.exit_code == 0
    assert "Ticketer deleted successfully" in result.output


def test_delete_ticketer_reports_request_error(mocker):
    mocker.patch("weni_cli.commands.ticketer_delete.Store.get", return_value=PROJECT_UUID)
    client = mocker.patch("weni_cli.commands.ticketer_delete.CLIClient")
    client.return_value.delete_ticketer.side_effect = RequestError("missing", status_code=404)

    result = _invoke(["ticketer", "delete", TICKETER_UUID, "--yes"])

    assert result.exit_code == 0
    assert "Error: missing" in result.output
