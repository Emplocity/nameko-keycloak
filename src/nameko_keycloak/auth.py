import logging
from typing import Any, Optional

from jwcrypto.common import JWException
from jwcrypto.jwt import JWTExpired
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
        logger.debug(f"Found access token in cookies: {cookie_name=}")
        return token
    elif "Authorization" in request.headers:
        header = request.headers["Authorization"]
        token = header.replace("Bearer ", "", 1)
        logger.debug("Found access token in Authorization header")
        return token
    logger.debug("Access token not found in request")
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
        logger.debug(f"AuthenticationService setup: {sso_cookie_prefix=}")

    def get_user_from_access_token(self, access_token: Token) -> Optional[User]:
        """
        Find a local User corresponding to Keycloak access token.
        """
        return self._get_user(access_token)

    def get_user_from_request(self, request: Request, **kwargs) -> Optional[User]:
        """
        Find a local User corresponding to some token in the HTTP request.
        """
        token = get_token_from_request(
            request, cookie_name=f"{self.sso_cookie_prefix}_access-token"
        )
        if not token:
            return None
        return self._get_user(token)

    def get_token_payload(self, access_token: Token) -> dict[str, Any]:
        try:
            return self.keycloak.decode_token(access_token)
        except JWTExpired:
            logger.debug("Failed to decode access token: token expired")
            return {}
        except JWException:
            logger.exception("Failed to decode access token")
            return {}

    def _get_user(self, access_token: Token) -> Optional[User]:
        token_payload = self.get_token_payload(access_token)
        if not token_payload:
            return None
        user = self.fetch_user(token_payload["email"], token_payload)
        logger.debug(f"User identified by token: {user=}")
        return user
