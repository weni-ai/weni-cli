import pytest
from weni_cli.clients.weni_client import DEFAULT_BASE_URL, WeniClient
from weni_cli.store import STORE_TOKEN_KEY, STORE_WENI_BASE_URL


@pytest.fixture
def mock_store(mocker):
    """Mock the Store class to return predefined values."""

    def _mock(token="test-token", base_url=DEFAULT_BASE_URL):
        def side_effect(key, default=None):
            if key == STORE_TOKEN_KEY:
                return token
            elif key == STORE_WENI_BASE_URL:
                return base_url
            return default

        mocker.patch("weni_cli.clients.weni_client.Store.get", side_effect=side_effect)
        return token, base_url

    return _mock


@pytest.fixture
def client(mock_store):
    """Create a WeniClient instance with mocked store."""
    mock_store()
    return WeniClient()


def test_init_with_default_values(mock_store):
    """Test initialization with default values."""
    token, base_url = mock_store()
    client = WeniClient()

    assert client.headers == {"Authorization": f"Bearer {token}"}
    assert client.base_url == base_url


def test_init_with_custom_base_url(mock_store):
    """Test initialization with custom base URL."""
    token, base_url = mock_store(base_url="https://custom.api.example.com")
    client = WeniClient()

    assert client.headers == {"Authorization": f"Bearer {token}"}
    assert client.base_url == base_url


def test_get_org_success(client, requests_mock):
    """Test successful retrieval of an organization."""
    org_uuid = "test-org-uuid"
    org_data = {"uuid": org_uuid, "name": "Test Organization"}

    requests_mock.get(f"{client.base_url}/v2/organizations/{org_uuid}/", json=org_data)

    result = client.get_org(org_uuid)

    assert result == org_data


def test_get_org_failure(client, requests_mock, mocker):
    """Test failed retrieval of an organization."""
    mock_echo = mocker.patch("rich_click.echo")
    org_uuid = "test-org-uuid"

    requests_mock.get(f"{client.base_url}/v2/organizations/{org_uuid}/", status_code=404)

    result = client.get_org(org_uuid)

    assert result is None
    mock_echo.assert_called_once_with("Failed to get organization")


def test_list_orgs_success_single_page(client, requests_mock):
    """Test listing organizations with a single page of results."""
    orgs_data = {
        "results": [{"uuid": "org-1", "name": "Organization 1"}, {"uuid": "org-2", "name": "Organization 2"}],
        "next": None,
    }

    requests_mock.get(f"{client.base_url}/v2/organizations/", json=orgs_data)

    next_url, orgs = client.list_orgs()

    assert next_url is None
    assert len(orgs) == 2
    assert orgs[0]["name"] == "Organization 1"
    assert orgs[1]["uuid"] == "org-2"


def test_list_orgs_success_multiple_pages(client, requests_mock):
    """Test listing organizations with multiple pages of results."""
    page1_data = {
        "results": [{"uuid": "org-1", "name": "Organization 1"}],
        "next": f"{client.base_url}/v2/organizations/?page=2",
    }

    page2_data = {"results": [{"uuid": "org-2", "name": "Organization 2"}], "next": None}

    requests_mock.get(f"{client.base_url}/v2/organizations/", json=page1_data)

    next_url, orgs = client.list_orgs()

    assert next_url == f"{client.base_url}/v2/organizations/?page=2"
    assert len(orgs) == 1
    assert orgs[0]["name"] == "Organization 1"

    # Test with the next page URL
    requests_mock.get(next_url, json=page2_data)

    next_url, more_orgs = client.list_orgs(next_url)

    assert next_url is None
    assert len(more_orgs) == 1
    assert more_orgs[0]["name"] == "Organization 2"


def test_list_orgs_failure(client, requests_mock, mocker):
    """Test failed listing of organizations."""
    mock_echo = mocker.patch("rich_click.echo")

    requests_mock.get(f"{client.base_url}/v2/organizations/", status_code=500)

    next_url, orgs = client.list_orgs()

    assert next_url is None
    assert orgs == []
    mock_echo.assert_called_once_with("Failed to list organizations")


def test_list_projects_with_org_uuid_success(client, requests_mock, mocker):
    """Test listing projects with a specific org UUID."""
    org_uuid = "test-org-uuid"
    org_data = {"uuid": org_uuid, "name": "Test Organization"}

    projects_data = {
        "results": [{"uuid": "project-1", "name": "Project 1"}, {"uuid": "project-2", "name": "Project 2"}],
        "next": None,
    }

    # Mock the get_org method to return org_data
    mocker.patch.object(client, "get_org", return_value=org_data)

    # Mock the projects endpoint
    requests_mock.get(f"{client.base_url}/v2/organizations/{org_uuid}/projects", json=projects_data)

    next_url, org_project_map = client.list_projects(org_uuid=org_uuid)

    assert next_url is None
    assert "Test Organization" in org_project_map
    assert len(org_project_map["Test Organization"]) == 2
    assert org_project_map["Test Organization"][0] == ("Project 1", "project-1")
    assert org_project_map["Test Organization"][1] == ("Project 2", "project-2")


def test_list_projects_with_org_uuid_failure_getting_org(client, mocker):
    """Test listing projects when get_org fails."""
    org_uuid = "test-org-uuid"

    # Mock the get_org method to return None (failure)
    mocker.patch.object(client, "get_org", return_value=None)

    next_url, org_project_map = client.list_projects(org_uuid=org_uuid)

    assert next_url is None
    assert org_project_map == {}


def test_list_projects_without_org_uuid_success(client, requests_mock, mocker):
    """Test listing projects without a specific org UUID."""
    orgs_data = {
        "results": [{"uuid": "org-1", "name": "Organization 1"}, {"uuid": "org-2", "name": "Organization 2"}],
        "next": None,
    }

    projects_data_org1 = {"results": [{"uuid": "project-1", "name": "Project 1"}], "next": None}

    projects_data_org2 = {
        "results": [{"uuid": "project-2", "name": "Project 2"}, {"uuid": "project-3", "name": "Project 3"}],
        "next": None,
    }

    # Mock the list_orgs method to return orgs_data
    mocker.patch.object(client, "list_orgs", return_value=(None, orgs_data["results"]))

    # Mock the projects endpoints
    requests_mock.get(f"{client.base_url}/v2/organizations/org-1/projects", json=projects_data_org1)
    requests_mock.get(f"{client.base_url}/v2/organizations/org-2/projects", json=projects_data_org2)

    next_url, org_project_map = client.list_projects()

    assert next_url is None
    assert "Organization 1" in org_project_map
    assert "Organization 2" in org_project_map
    assert len(org_project_map["Organization 1"]) == 1
    assert len(org_project_map["Organization 2"]) == 2
    assert org_project_map["Organization 1"][0] == ("Project 1", "project-1")
    assert org_project_map["Organization 2"][0] == ("Project 2", "project-2")
    assert org_project_map["Organization 2"][1] == ("Project 3", "project-3")


def test_list_projects_without_org_uuid_empty_orgs(client, mocker):
    """Test listing projects when no orgs are found."""
    mock_echo = mocker.patch("rich_click.echo")

    # Mock the list_orgs method to return empty list
    mocker.patch.object(client, "list_orgs", return_value=(None, []))

    next_url, org_project_map = client.list_projects()

    assert next_url is None
    assert org_project_map == {}
    mock_echo.assert_called_once_with("No orgs found")


def test_list_projects_failure_getting_projects(client, requests_mock, mocker):
    """Test listing projects when getting projects fails."""
    mock_echo = mocker.patch("rich_click.echo")

    orgs_data = {"results": [{"uuid": "org-1", "name": "Organization 1"}], "next": None}

    # Mock the list_orgs method to return orgs_data
    mocker.patch.object(client, "list_orgs", return_value=(None, orgs_data["results"]))

    # Mock the projects endpoint to fail
    requests_mock.get(f"{client.base_url}/v2/organizations/org-1/projects", status_code=500)

    next_url, org_project_map = client.list_projects()

    assert next_url is None
    assert org_project_map == {}
    mock_echo.assert_called_once_with("Failed to list projects")


def test_list_projects_with_paginated_projects(client, requests_mock, mocker):
    """Test listing projects with paginated project results."""
    orgs_data = {"results": [{"uuid": "org-1", "name": "Organization 1"}], "next": None}

    projects_page1 = {
        "results": [{"uuid": "project-1", "name": "Project 1"}],
        "next": f"{client.base_url}/v2/organizations/org-1/projects?page=2",
    }

    projects_page2 = {"results": [{"uuid": "project-2", "name": "Project 2"}], "next": None}

    # Mock the list_orgs method to return orgs_data
    mocker.patch.object(client, "list_orgs", return_value=(None, orgs_data["results"]))

    # Mock the projects endpoints with pagination
    requests_mock.get(f"{client.base_url}/v2/organizations/org-1/projects", json=projects_page1)
    requests_mock.get(f"{client.base_url}/v2/organizations/org-1/projects?page=2", json=projects_page2)

    next_url, org_project_map = client.list_projects()

    assert next_url is None
    assert "Organization 1" in org_project_map
    assert len(org_project_map["Organization 1"]) == 2
    assert org_project_map["Organization 1"][0] == ("Project 1", "project-1")
    assert org_project_map["Organization 1"][1] == ("Project 2", "project-2")
