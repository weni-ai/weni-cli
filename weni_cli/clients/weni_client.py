import click
import requests

from weni_cli.store import STORE_TOKEN_KEY, STORE_WENI_BASE_URL, Store

DEFAULT_BASE_URL = "https://api.weni.ai"


class WeniClient:
    base_url = None
    headers = None

    def __init__(self):
        store = Store()
        self.headers = {"Authorization": f"Bearer {store.get(STORE_TOKEN_KEY)}"}
        self.base_url = store.get(STORE_WENI_BASE_URL, DEFAULT_BASE_URL)

    def get_org(self, org_uuid):
        url = f"{self.base_url}/v2/organizations/{org_uuid}/"

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            click.echo("Failed to get organization")
            return

        return response.json()

    def list_orgs(self, url=None) -> tuple[str, list]:
        url = f"{self.base_url}/v2/organizations/" if not url else url
        orgs = []

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            click.echo("Failed to list organizations")
            return None, []

        orgs += response.json().get("results", [])
        next_url = response.json().get("next", None)

        return next_url, orgs

    def list_projects(self, org_uuid=None, next_orgs_page_url=None) -> tuple[str, dict]:
        orgs = []
        next_url = None
        if org_uuid:
            org = self.get_org(org_uuid)

            if not org:
                return None, {}

            orgs.append(org)
        else:
            next_url, orgs = self.list_orgs(next_orgs_page_url)

        if not orgs:
            click.echo("No orgs found")
            return None, {}

        org_project_map = {}

        for org in orgs:
            if org["name"] not in org_project_map:
                org_project_map[org["name"]] = []

            projects = []
            url = f"{self.base_url}/v2/organizations/{org['uuid']}/projects"

            while url:
                response = requests.get(url, headers=self.headers)

                if response.status_code != 200:
                    click.echo("Failed to list projects")
                    return None, {}

                projects += response.json().get("results", [])
                url = response.json().get("next", None)

            for project in projects:
                org_project_map[org["name"]].append((project["name"], project["uuid"]))

        return next_url, org_project_map
