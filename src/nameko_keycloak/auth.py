import logging
from typing import Optional

from jose import JOSEError
from keycloak import KeycloakOpenID
from werkzeug import Request

from .types import FetchUserCallable, Token, User

logger = logging.getLogger(__name__)


def get_token_from_request(request: Request) -> Token:
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
        return self._get_user(token)

    def _get_user(self, access_token: Token) -> Optional[User]:
        try:
            token_payload = self.keycloak.decode_token(
                access_token, self.keycloak.certs()
            )
        except JOSEError:
            logger.exception("Failed to decode access token")
            return None
        return self.fetch_user(token_payload["email"])
