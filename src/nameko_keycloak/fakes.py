import logging
from typing import Any, Dict, List

from jose import JOSEError
from keycloak.exceptions import KeycloakError

from .types import Token, TokenPayload

logger = logging.getLogger(__name__)


class FakeKeycloak:
    """
    Fake to be used wherever tests need to interact with Keycloak.

    This class emulates a few APIs of ``KeycloakOpenID`` that we use for
    SSO workflow.

    We're working under a very important assumption here: You need to pass
    user's email as ``code`` when generating their token. This is obviously
    not true in real life where Keycloak manages generating secure tokens
    from one-time codes, but here it simplifies a lot.

    The Keycloak user database is simulated by a key-value storage where you
    insert an item when calling :meth:`token`, and fetch from storage when
    calling :meth:`decode_token` or :meth:`refresh_token`.
    """

    def __init__(self):
        self.token_payloads: Dict[Token, TokenPayload] = {}

    def auth_url(self, **kwargs) -> str:
        return "http://keycloak.url"

    def token(self, code: str, **kwargs) -> TokenPayload:
        email = code
        token = f"token_{email}"
        token_payload = {
            "email": email,
            "access_token": token,
            "expires_in": "EXP",
            # this is not semantically correct, but satisifes other uses of
            # refresh_token, such as logout()
            "refresh_token": email,
            "refresh_expires_in": "REXP",
            "refresh_token_url": "http://keycloak.url/refresh",
        }
        self.token_payloads[token] = token_payload
        return token_payload

    def decode_token(self, token: Token, certs: List[Any]) -> TokenPayload:
        logger.info(f"Looking up {token} in {self.token_payloads}")
        try:
            return self.token_payloads[token]
        except KeyError:
            raise JOSEError("Missing user")

    def refresh_token(self, refresh_token: Token, **kwargs) -> TokenPayload:
        token = f"token_{refresh_token}"
        logger.info(f"Looking up {token} in {self.token_payloads}")
        try:
            return self.token_payloads[token]
        except KeyError:
            raise KeycloakError("Missing user")

    def logout(self, refresh_token: Token) -> None:
        token = f"token_{refresh_token}"
        del self.token_payloads[token]

    def certs(self) -> List[Any]:
        return []
