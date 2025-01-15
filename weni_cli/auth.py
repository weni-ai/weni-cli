import requests

from weni_cli.store import (
    STORE_KEYCLOAK_CLIENT_ID,
    STORE_KEYCLOAK_REALM,
    STORE_KEYCLOAK_URL,
    Store,
)
from weni_cli.wsgi import DEFAULT_PORT


DEFAULT_KEYCLOAK_URL = "https://accounts.weni.ai/auth"
DEFAULT_KEYCLOAK_REALM = "weni"
DEFAULT_KEYCLOAK_CLIENT_ID = "weni-cli"


class Auth:
    keycloak_url = None
    realm = None
    client_id = None
    response_type = "code"
    redirect_uri = f"http://localhost:{DEFAULT_PORT}/sso-callback"

    def __init__(self):
        store = Store()
        self.keycloak_url = store.get(STORE_KEYCLOAK_URL, DEFAULT_KEYCLOAK_URL)
        self.realm = store.get(STORE_KEYCLOAK_REALM, DEFAULT_KEYCLOAK_REALM)
        self.client_id = store.get(STORE_KEYCLOAK_CLIENT_ID, DEFAULT_KEYCLOAK_CLIENT_ID)

    def get_login_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/auth?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type={self.response_type}"

    def exchange_code(self, code) -> str:
        token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"

        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        response = requests.post(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            return None

        return response.json().get("access_token", None)
