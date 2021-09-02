import json
import logging
from pathlib import Path

from keycloak import KeycloakOpenID
from nameko.extensions import DependencyProvider

logger = logging.getLogger(__name__)


class KeycloakProvider(DependencyProvider):
    def __init__(self, keycloak_path: Path):
        self.keycloak_path = keycloak_path

    def setup(self) -> None:
        config = json.loads(self.keycloak_path.read_text())
        self.provider = KeycloakOpenID(
            server_url=config.get("auth-server-url"),
            client_id=config.get("resource"),
            realm_name=config.get("realm"),
            client_secret_key=config.get("credentials").get("secret"),
            verify=True,
        )

    def get_dependency(self, worker_ctx) -> KeycloakOpenID:
        return self.provider
