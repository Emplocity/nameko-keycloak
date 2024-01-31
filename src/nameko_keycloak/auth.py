import logging
from typing import Any, Dict, Optional

from jose import JOSEError
from keycloak import KeycloakOpenID
from werkzeug import Request

from .types import FetchUserCallable, Token, User

logger = logging.getLogger(__name__)


def get_token_from_request(request: Request, cookie_name: str) -> Optional[Token]:
    """
    Try to locate access token in the incoming request.

    The function first reads access token from a (HttpOnly) cookie sent by
    a browser. If such cookie does not exist, we try a standard OAuth2 approach
    with token in header (sent by Oauth2 clients like Insomnia).
    """
    if token := request.cookies.get(cookie_name):
        return token
    elif "Authorization" in request.headers:
        header = request.headers["Authorization"]
        token = header.replace("Bearer ", "", 1)
        return token
    return None


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

    def __init__(
        self,
        keycloak: KeycloakOpenID,
        fetch_user: FetchUserCallable,
        sso_cookie_prefix: str = "nameko-keycloak",
    ):
        self.keycloak = keycloak
        self.fetch_user = fetch_user
        self.sso_cookie_prefix = sso_cookie_prefix

    def get_user_from_access_token(self, access_token: Token) -> Optional[User]:
        """
        Find a local User corresponding to Keycloak access token.
        """
        return self._get_user(access_token)

    def get_user_from_request(
        self, request: Request, cookie_name="access-token", **kwargs
    ) -> Optional[User]:
        """
        Find a local User corresponding to some token in the HTTP request.
        """
        token = get_token_from_request(
            request, cookie_name=f"{self.sso_cookie_prefix}_access-token"
        )
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
