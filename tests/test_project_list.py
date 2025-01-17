import pytest
import requests_mock

from click.testing import CliRunner
from weni_cli.cli import project


@pytest.fixture(autouse=True)
def slow_down_tests(mocker):
    mocker.resetall()


@requests_mock.Mocker(kw="requests_mock")
def test_project_list(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")
    requests_mock.get(
        "https://api.weni.ai/v2/organizations/",
        status_code=200,
        json={
            "next": "https://api.weni.ai/v2/organizations/?page=2",
            "results": [{"name": "org1", "uuid": "org1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/org1-uuid/projects",
        status_code=200,
        json={
            "next": "https://api.weni.ai/v2/organizations/org1-uuid/projects?page=2",
            "results": [{"name": "project1", "uuid": "project1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/org1-uuid/projects?page=2",
        status_code=200,
        json={"results": [{"name": "project2", "uuid": "project2-uuid"}]},
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/?page=2",
        status_code=200,
        json={"results": [{"name": "org2", "uuid": "org2-uuid"}]},
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/org2-uuid/projects",
        status_code=200,
        json={"results": [{"name": "project3", "uuid": "project3-uuid"}]},
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("click.launch", return_value=None)
        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://api.weni.ai"])

        result = runner.invoke(project, ["list"], terminal_width=80, input="p\n")

        assert result.exit_code == 0
        assert (
            result.output
            == 'Fetching projects... Please wait\n\nOrg org1\n- project1  project1-uuid  \n- project2  project2-uuid  \n\nPress "q" to quit or press "p" to load more projects [p]: p\n\nOrg org2\n- project3  project3-uuid  \n\n'
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_list_stop(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")
    requests_mock.get(
        "https://api.weni.ai/v2/organizations/",
        status_code=200,
        json={
            "next": "https://api.weni.ai/v2/organizations/?page=2",
            "results": [{"name": "org1", "uuid": "org1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/org1-uuid/projects",
        status_code=200,
        json={
            "next": "https://api.weni.ai/v2/organizations/org1-uuid/projects?page=2",
            "results": [{"name": "project1", "uuid": "project1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/org1-uuid/projects?page=2",
        status_code=200,
        json={"results": [{"name": "project2", "uuid": "project2-uuid"}]},
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("click.launch", return_value=None)
        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://api.weni.ai"])

        result = runner.invoke(project, ["list"], terminal_width=80, input="q\n")

        assert result.exit_code == 0
        assert (
            result.output
            == 'Fetching projects... Please wait\n\nOrg org1\n- project1  project1-uuid  \n- project2  project2-uuid  \n\nPress "q" to quit or press "p" to load more projects [p]: q\n'
        )


def test_project_list_no_token(mocker):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(project, ["list"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == "Missing login authorization, please login first\n"


def test_project_list_error_org_list(mocker):
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://api.weni.ai"])

        result = runner.invoke(project, ["list"], terminal_width=80)

        assert result.exit_code == 0
        assert (
            result.output
            == "Fetching projects... Please wait\nFailed to list organizations\nNo orgs found\nAn error occurred: Failed to list projects\n"
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_list_error_project_list(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")
    requests_mock.get(
        "https://api.weni.ai/v2/organizations/",
        status_code=200,
        json={
            "next": "https://api.weni.ai/v2/organizations/?page=2",
            "results": [{"name": "org1", "uuid": "org1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/org1-uuid/projects",
        status_code=400,
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("click.launch", return_value=None)
        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://api.weni.ai"])

        result = runner.invoke(project, ["list"], terminal_width=80, input="p\n")

        assert result.exit_code == 0
        assert (
            result.output
            == "Fetching projects... Please wait\nFailed to list projects\nAn error occurred: Failed to list projects\n"
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_list_error_org_list_on_page_2(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")
    requests_mock.get(
        "https://api.weni.ai/v2/organizations/",
        status_code=200,
        json={
            "next": "https://api.weni.ai/v2/organizations/?page=2",
            "results": [{"name": "org1", "uuid": "org1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/org1-uuid/projects",
        status_code=200,
        json={
            "results": [{"name": "project1", "uuid": "project1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/?page=2",
        status_code=400,
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("click.launch", return_value=None)
        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://api.weni.ai"])

        result = runner.invoke(project, ["list"], terminal_width=80, input="p\n")

        assert result.exit_code == 0
        assert (
            result.output
            == 'Fetching projects... Please wait\n\nOrg org1\n- project1  project1-uuid  \n\nPress "q" to quit or press "p" to load more projects [p]: p\nFailed to list organizations\nNo orgs found\nAn error occurred: Failed to list projects\n'
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_list_error_project_list_on_page_2(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")
    requests_mock.get(
        "https://api.weni.ai/v2/organizations/",
        status_code=200,
        json={
            "next": "https://api.weni.ai/v2/organizations/?page=2",
            "results": [{"name": "org1", "uuid": "org1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/org1-uuid/projects",
        status_code=200,
        json={
            "results": [{"name": "project1", "uuid": "project1-uuid"}],
        },
    )

    requests_mock.get(
        "https://api.weni.ai/v2/organizations/?page=2",
        status_code=200,
        json={
            "results": [{"name": "org2", "uuid": "org2-uuid"}],
        },
    )

    requests_mock.get("https://api.weni.ai/v2/organizations/org2-uuid/projects", status_code=400)

    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("click.launch", return_value=None)
        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://api.weni.ai"])

        result = runner.invoke(project, ["list"], terminal_width=80, input="p\n")

        assert result.exit_code == 0
        assert (
            result.output
            == 'Fetching projects... Please wait\n\nOrg org1\n- project1  project1-uuid  \n\nPress "q" to quit or press "p" to load more projects [p]: p\nFailed to list projects\nAn error occurred: Failed to list projects\n'
        )
