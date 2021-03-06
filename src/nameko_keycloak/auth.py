import logging
from typing import Any, Dict, Optional

from jose import JOSEError
from keycloak import KeycloakOpenID
from werkzeug import Request

from .types import FetchUserCallable, Token, User

logger = logging.getLogger(__name__)


def get_token_from_request(request: Request) -> Optional[Token]:
    if "Authorization" not in request.headers:
        return None
    header = request.headers["Authorization"]
    token = header.replace("Bearer ", "", 1)
    return token


class AuthenticationService:
    """
    Provides a way to retrieve properly authenticated user from a request.

    As we store user credentials in an external service (Keycloak), this service
    checks for two things:

     - first, validate access token found in the request
     - if Keycloak confirms the token is valid, look up local User

    Only when the user exists in both Keycloak and local database, we consider
    them authenticated.
    """

    def __init__(self, keycloak: KeycloakOpenID, fetch_user: FetchUserCallable):
        self.keycloak = keycloak
        self.fetch_user = fetch_user

    def get_user_from_access_token(self, access_token: Token) -> Optional[User]:
        """
        Find a local User corresponding to Keycloak access token.
        """
        return self._get_user(access_token)

    def get_user_from_request(self, request: Request, **kwargs) -> Optional[User]:
        """
        Find a local User corresponding to some token in the HTTP request.
        """
        token = get_token_from_request(request)
        if not token:
            return None
        return self._get_user(token)

    def get_token_payload(self, access_token: Token) -> Dict[str, Any]:
        try:
            return self.keycloak.decode_token(access_token, self.keycloak.certs())
        except JOSEError:
            logger.exception("Failed to decode access token")
            return {}

    def _get_user(self, access_token: Token) -> Optional[User]:
        token_payload = self.get_token_payload(access_token)
        if not token_payload:
            return None
        return self.fetch_user(token_payload["email"], token_payload)
