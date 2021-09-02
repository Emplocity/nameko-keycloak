import enum
import json
import logging
from typing import Optional

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response

from .auth import AuthenticationService
from .types import FetchUserCallable, Token, TokenPayload, User

logger = logging.getLogger(__name__)


class HookMethod(enum.Enum):
    # TODO: document how these map to service methods
    SUCCESS = "keycloak_success"
    FAILURE = "keycloak_failure"


class KeycloakSsoServiceMixin:
    """
    Add this to your nameko service to provide SSO authentication with Keycloak.

    This mixin exposes five methods prefixed with ``keycloak_``, which you
    should use in your HTTP service. Delegate from your entrypoints like this:

        @http("GET", "/login")
        def login_sso(self, request):
            return self.keycloak_login_sso(request)

    This way it is up to you to control the URL routes and any middleware
    or extra request handling (such as CORS headers).

    Expected service dependencies or class attributes:

     - ``keycloak`` which must be an instance of
        :class:`dependencies.KeycloakProvider`
     - ``sso_cookie_prefix`` - a string that will be used to namespace cookies
        (useful when there are multiple SSO-enabled apps hosted on same domain)
     - ``sso_login_url`` - absolute URL to handler which delegates to :meth:`keycloak_login_sso`
     - ``sso_token_url`` - absolute URL to handler which delegates to :meth:`keycloak_token_sso`
     - ``sso_refresh_token_url`` - absolute URL to handler which delegates to :meth:`keycloak_refresh_token_sso`
     - ``frontend_url`` - absolute URL to a user-facing web app that
        communicates with this backend service

    TODO: document ``fetch_user`` and hooks

    """

    keycloak: KeycloakOpenID
    sso_cookie_prefix: str = "nameko-keycloak"
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
        Generates a new access token, given a valid refresh token.
        """
        token = json.loads(request.data)["token"]

        try:
            token_payload = self.keycloak.refresh_token(refresh_token=token)
        except KeycloakError:
            self.run_hook(HookMethod.FAILURE)
            return Response("Invalid", status=401)

        response = Response(
            json.dumps({"access_token": token_payload["access_token"]}),
            status=200,
            content_type="application/json",
        )
        return self._setup_response_cookie(response, token_payload)

    def keycloak_validate_token_sso(self, request: Request, token: Token) -> Response:
        """
        Checks that access token is valid and a corresponding local User exists.
        """
        auth = AuthenticationService(self.keycloak, self.fetch_user)
        user = auth.get_user_from_access_token(token)
        if not user:
            return Response("Invalid", status=401)
        return Response("Valid", status=200)

    def keycloak_logout(self, request: Request) -> Response:
        """
        Invalidates session in Keycloak and redirects to login form.

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
        return redirect(self.sso_login_url)

    def _setup_response_cookie(
        self, response: Response, token_payload: TokenPayload
    ) -> Response:
        response.set_cookie(
            key=f"{self.sso_cookie_prefix}_access-token",
            value=token_payload["access_token"],
        )
        response.set_cookie(
            key=f"{self.sso_cookie_prefix}_expires-in",
            value=str(token_payload["expires_in"]),
        )
        response.set_cookie(
            key=f"{self.sso_cookie_prefix}_refresh-token",
            value=token_payload["refresh_token"],
        )
        response.set_cookie(
            key=f"{self.sso_cookie_prefix}_refresh-expires-in",
            value=str(token_payload["refresh_expires_in"]),
        )
        response.set_cookie(
            key=f"{self.sso_cookie_prefix}_refresh-token-url",
            value=self.sso_refresh_token_url,
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
