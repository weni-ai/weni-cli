import click
import os
import json

from pathlib import Path

STORE_TOKEN_KEY = "token"
STORE_PROJECT_UUID_KEY = "project_uuid"
STORE_WENI_BASE_URL = "weni_base_url"
STORE_NEXUS_BASE_URL = "nexus_base_url"
STORE_KEYCLOAK_URL = "keycloak_url"
STORE_KEYCLOAK_REALM = "keycloak_realm"
STORE_KEYCLOAK_CLIENT_ID = "keycloak_client_id"


class Store:
    file_path = f"{Path.home()}{os.sep}.weni_cli"

    # Validates that the file exists, if it does not exist, it creates it with an empty dictionary
    def __init__(self):
        with click.open_file(self.file_path, "a+") as file:
            file.seek(0)
            content = file.read()
            if not content:
                file.write("{}")

            file.close()

    def get(self, key, default=None):
        with click.open_file(self.file_path, "r") as file:
            content = json.loads(file.read())
            file.close()
            return content.get(key, default)

    def set(self, key, value):
        content = {}
        with click.open_file(self.file_path, "r") as file:
            content = json.loads(file.read())
            file.close()

        with click.open_file(self.file_path, "w") as file:
            content[key] = value
            file.write(json.dumps(content))
            file.close()

        return True
