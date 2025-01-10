import requests
import json

from weni_cli.store import STORE_NEXUS_BASE_URL, STORE_TOKEN_KEY, Store

DEFAULT_BASE_URL = "https://nexus.weni.ai"


class NexusClient:
    base_url = None
    headers = None

    def __init__(self):
        store = Store()
        self.headers = {"Authorization": f"Bearer {store.get(STORE_TOKEN_KEY)}"}
        self.base_url = store.get(STORE_NEXUS_BASE_URL, DEFAULT_BASE_URL)

    def push_agents(self, project_uuid, agents_definition, skill_files):
        url = f"{self.base_url}/api/agents/push"

        data = {
            "project_uuid": project_uuid,
            "agents": json.dumps(agents_definition),
        }

        return requests.post(url, headers=self.headers, data=data, files=skill_files)
