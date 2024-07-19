import enum
import json
import logging
from typing import Optional

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response

from .auth import AuthenticationService
from .types import FetchUserCallable, TokenPayload, User

logger = logging.getLogger(__name__)


class HookMethod(enum.Enum):
    SUCCESS = "keycloak_success"
    FAILURE = "keycloak_failure"


class KeycloakSsoServiceMixin:
    """
    Add this to your nameko service to provide SSO authentication with Keycloak.

    Expected service dependencies or class attributes:

     - ``keycloak`` which must be an instance of :class:`~nameko_keycloak.dependencies.KeycloakProvider`
     - ``sso_cookie_prefix`` - a string that will be used to namespace cookies (useful when there are multiple SSO-enabled apps hosted on same domain)
     - ``sso_cookie_path`` - path part of the URL of your application, set as Path cookie attribute
     - ``sso_login_url`` - absolute URL to handler which delegates to :meth:`keycloak_login_sso`
     - ``sso_token_url`` - absolute URL to handler which delegates to :meth:`keycloak_token_sso`
     - ``sso_refresh_token_url`` - absolute URL to handler which delegates to :meth:`keycloak_refresh_token_sso`
     - ``frontend_url`` - absolute URL to a user-facing web app that communicates with this backend service
    """

    keycloak: KeycloakOpenID
    sso_cookie_prefix: str = "nameko-keycloak"
    sso_cookie_path: str = "/"
    sso_login_url: str = "/login-sso"
    sso_token_url: str = "/token-sso"
    sso_refresh_token_url: str = "/refresh-token-sso"
    frontend_url: str = "/"

    def keycloak_login_sso(self, request: Request) -> Response:
        """
        Redirects to SSO login form configured to return back to HTTP service.
        """
        return redirect(self.keycloak.auth_url(redirect_uri=self.sso_token_url))

    def keycloak_token_sso(self, request: Request) -> Response:
        """
        Handles redirect from successful login in SSO.

        The SSO passes a `code` query string parameter which we then use to
        generate a OAuth access token. We make sure that a local User exists
        before they are allowed to reach frontend URL. If all goes well, the
        access token and several other metadata are stored in cookies.
        """
        # annotate bound method here, otherwise mypy can't resolve self
        self.fetch_user: FetchUserCallable
        auth = AuthenticationService(self.keycloak, self.fetch_user)
        if request.args.get("code"):
            token = self.keycloak.token(
                code=request.args.get("code"),
                grant_type=["authorization_code"],
                redirect_uri=self.sso_token_url,
            )
            user = auth.get_user_from_access_token(access_token=token["access_token"])
            if not user:
                return Response("Unauthorized", status=401)
            self.run_hook(HookMethod.SUCCESS, user)
            response = redirect(self.frontend_url)
            return self._setup_response_cookie(response, token)
        return Response("Empty request")

    def keycloak_refresh_token_sso(self, request: Request) -> Response:
        """
        Generates a new access token, given a cookie with a valid refresh token.
        """
        refresh_token = request.cookies.get(f"{self.sso_cookie_prefix}_refresh-token")
        if not refresh_token:
            logger.warning("No refresh token found in cookies")
            self.run_hook(HookMethod.FAILURE)
            return Response("Invalid", status=401)

        try:
            token_payload = self.keycloak.refresh_token(refresh_token=refresh_token)
        except KeycloakError as e:
            # Decode Keycloak error details and decide if it's serious enough
            # to call failure hook
            error_code: str = ""
            try:
                payload = json.loads(e.response_body.decode("utf-8"))
                error_code = payload["error"]
            except Exception:
                logger.exception("Failed to decode Keycloak error details")
            if error_code == "invalid_grant":
                # This is a normal situation, refresh token exists but expired.
                # In this case frontend should redirect to login page.
                logger.debug("Refresh token expired")
            else:
                self.run_hook(HookMethod.FAILURE)
            return Response("Invalid", status=401)

        response = Response(
            json.dumps({"access_token": token_payload["access_token"]}),
            status=200,
            content_type="application/json",
        )
        return self._setup_response_cookie(response, token_payload)

    def keycloak_validate_token_sso(self, request: Request) -> Response:
        """
        Checks that access token is valid and a corresponding local User exists.
        """
        token = request.cookies.get(f"{self.sso_cookie_prefix}_access-token")
        if not token:
            logger.warning("No access token found in cookies")
            return Response("Invalid", status=401)
        auth = AuthenticationService(self.keycloak, self.fetch_user)
        user = auth.get_user_from_access_token(token)
        if not user:
            return Response("Invalid", status=401)
        return Response("Valid", status=200)

    def keycloak_logout(self, request: Request) -> Response:
        """
        Invalidates session in Keycloak, deletes cookies and redirects to login.

        .. note::
            Keycloak logout API invalidates only refresh token, not access
            token. This is by design, as access tokens should be short lived
            anyway.
        """
        refresh_token = request.cookies.get(f"{self.sso_cookie_prefix}_refresh-token")
        if not refresh_token:
            logger.warning("No refresh token found in cookies")
        try:
            self.keycloak.logout(refresh_token)
            logger.info("Logged out and invalidated Keycloak refresh token")
        except KeycloakError:
            self.run_hook(HookMethod.FAILURE)
        response = redirect(self.sso_login_url)
        response.delete_cookie(
            key=f"{self.sso_cookie_prefix}_access-token",
            path=self.sso_cookie_path,
        )
        response.delete_cookie(
            key=f"{self.sso_cookie_prefix}_refresh-token",
            path=self.sso_cookie_path,
        )
        return response

    def _setup_response_cookie(
        self, response: Response, token_payload: TokenPayload
    ) -> Response:
        response.set_cookie(
            key=f"{self.sso_cookie_prefix}_access-token",
            value=token_payload["access_token"],
            secure=True,
            httponly=True,
            path=self.sso_cookie_path,
        )
        response.set_cookie(
            key=f"{self.sso_cookie_prefix}_refresh-token",
            value=token_payload["refresh_token"],
            secure=True,
            httponly=True,
            path=self.sso_cookie_path,
        )
        return response

    def run_hook(self, hook_method: HookMethod, user: Optional[User] = None) -> None:
        instance_method = getattr(self, hook_method.value, None)
        if instance_method is None:
            logger.warning(
                f"Failed to call hook, {self.__class__} doesn't implement {hook_method.value} method"
            )
            return
        instance_method(user) if user else instance_method()
