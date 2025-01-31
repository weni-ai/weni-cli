import os
import requests_mock
import pytest

from click.testing import CliRunner

from weni_cli.cli import project
from weni_cli.commands.init import (
    SAMPLE_AGENT_DEFINITION_YAML,
    SAMPLE_ORDER_STATUS_SKILL_PY,
    SAMPLE_ORDER_DETAILS_SKILL_PY,
    SKILLS_FOLDER,
)


@pytest.fixture(autouse=True)
def slow_down_tests(mocker):
    mocker.resetall()


def create_mocked_files():
    with open("agents.json", "w") as f:
        f.write(SAMPLE_AGENT_DEFINITION_YAML)

    try:
        os.mkdir(SKILLS_FOLDER)
        os.mkdir(f"{SKILLS_FOLDER}/order_status")
        os.mkdir(f"{SKILLS_FOLDER}/order_details")
    except FileExistsError:
        pass

    with open(f"{SKILLS_FOLDER}/order_status/lambda_function.py", "w") as f:
        f.write(SAMPLE_ORDER_STATUS_SKILL_PY)

    with open(f"{SKILLS_FOLDER}/order_details/lambda_function.py", "w") as f:
        f.write(SAMPLE_ORDER_DETAILS_SKILL_PY)

    with open(f"{SKILLS_FOLDER}/order_details/requirements.txt", "w") as f:
        f.write("")


@requests_mock.Mocker(kw="requests_mock")
def test_project_push(mocker, **kwargs):

    requests_mock = kwargs.get("requests_mock")
    requests_mock.post(
        "https://nexus.weni.ai/api/agents/push",
        status_code=200,
        headers={"Content-Type": "multipart/form-data"},
        json={"message": "Successfully pushed agents"},
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://nexus.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == "Definition pushed successfully\n"


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_file_not_found(mocker, **kwargs):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)
        assert result.exit_code == 2
        assert (
            result.output
            == "Usage: project push [OPTIONS] DEFINITION\nTry 'project push --help' for help.\n\nError: Invalid value for 'DEFINITION': File 'agents.json' does not exist.\n"
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_project_not_found(mocker, **kwargs):

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()

        mocker.patch("weni_cli.store.Store.get", side_effect=[""])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)
        assert result.exit_code == 0
        assert result.output == "No project selected, please select a project first\n"


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_error(mocker, **kwargs):

    requests_mock = kwargs.get("requests_mock")

    requests_mock.post(
        "https://nexus.weni.ai/api/agents/push",
        status_code=400,
        json={"message": "Failed to push agents"},
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://nexus.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == 'Failed to push definition, error: {"message": "Failed to push agents"}\n'


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_invalid_definition(mocker, **kwargs):

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("agents.json", "w") as f:
            f.write('agents:\ntest: -123\n  name: "Jon Snow"')

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://nexus.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert (
            result.output
            == 'Failed to parse definition file: mapping values are not allowed here\n  in "agents.json", line 3, column 7\n'
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_empty_definition(mocker, **kwargs):

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("agents.json", "w") as f:
            f.write("")

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://nexus.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == "Error: Empty definition file\n"


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_missing_skill_file(mocker, **kwargs):

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("agents.json", "w") as f:
            f.write(SAMPLE_AGENT_DEFINITION_YAML)

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://nexus.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == "Failed to load skill file: Folder skills/order_status not found\n"
