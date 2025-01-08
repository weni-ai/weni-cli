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

    def list_orgs(self) -> list:
        url = f"{self.base_url}/v2/organizations/"

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            click.echo("Failed to list organizations")
            return

        return response.json().get("results", [])

    def list_projects(self, org_uuid=None) -> dict:
        orgs = []
        if org_uuid:
            org = self.get_org(org_uuid)

            if not org:
                return {}

            orgs.append(org)
        else:
            orgs = self.list_orgs()

        if not orgs:
            click.echo("No orgs found")
            return {}

        org_project_map = {}

        for org in orgs:
            if org["name"] not in org_project_map:
                org_project_map[org["name"]] = []

            url = f"{self.base_url}/v2/organizations/{org['uuid']}/projects"

            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                click.echo("Failed to list projects")
                return {}

            projects = response.json().get("results", [])

            for project in projects:
                org_project_map[org["name"]].append((project["name"], project["uuid"]))

        return org_project_map
