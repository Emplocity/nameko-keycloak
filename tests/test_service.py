import json
from typing import Optional

import pytest
from keycloak.exceptions import KeycloakError
from nameko.testing.services import worker_factory
from nameko.web.handlers import http
from werkzeug.http import parse_cookie
from werkzeug.wrappers import Request, Response

from nameko_keycloak.dependencies import KeycloakProvider
from nameko_keycloak.fakes import FakeKeycloak
from nameko_keycloak.service import KeycloakSsoServiceMixin

from .models import USERS, User


class MyService(KeycloakSsoServiceMixin):
    name = "my_service"
    keycloak = KeycloakProvider("./keycloak.json")
    sso_cookie_prefix = "my-service"
    sso_login_url = "/login-sso"
    sso_token_url = "/token-sso"
    sso_refresh_token_url = "/refresh-token-sso"
    frontend_url = "/frontend"

    @http("GET", "/login-sso")
    def login_sso(self, request: Request) -> Response:
        return self.keycloak_login_sso(request)

    @http("GET", "/token-sso")
    def token_sso(self, request: Request) -> Response:
        return self.keycloak_token_sso(request)

    @http("POST", "/refresh-token-sso")
    def refresh_token_sso(self, request: Request) -> Response:
        return self.keycloak_refresh_token_sso(request)

    @http("GET", "/validate-token-sso/<token>")
    def validate_token_sso(self, request: Request, token: str) -> Response:
        return self.keycloak_validate_token_sso(request, token)

    @http("GET", "/logout")
    def logout(self, request: Request) -> Response:
        return self.keycloak_logout(request)

    def fetch_user(self, email: str) -> Optional[User]:
        return USERS.get(email)


@pytest.fixture
def my_service():
    return worker_factory(MyService, keycloak=FakeKeycloak())


def test_login_sso_redirect_user(my_service, request_factory):
    request = request_factory()
    response = my_service.login_sso(request)
    assert response.status_code == 302


def test_token_sso_set_cookies(my_service, request_factory):
    user = USERS["bob@example.com"]
    request = request_factory(args={"code": user.email})

    response = my_service.token_sso(request)

    assert response.headers["Location"] == MyService.frontend_url
    cookies_payload = {}
    for cookie in response.headers.getlist("Set-Cookie"):
        cookies_payload = {**cookies_payload, **parse_cookie(cookie)}
    assert f"{MyService.sso_cookie_prefix}_access-token" in cookies_payload
    assert f"{MyService.sso_cookie_prefix}_refresh-token" in cookies_payload


def test_refresh_token_sso(my_service, request_factory):
    user = USERS["bob@example.com"]
    # ensure user "exists" in keycloak
    token_payload = my_service.keycloak.token(code=user.email)

    request = request_factory(json={"token": user.email})
    response = my_service.refresh_token_sso(request)

    cookies_payload = {}
    for cookie in response.headers.getlist("Set-Cookie"):
        cookies_payload = {**cookies_payload, **parse_cookie(cookie)}
    assert f"{MyService.sso_cookie_prefix}_access-token" in cookies_payload
    assert f"{MyService.sso_cookie_prefix}_refresh-token" in cookies_payload
    response_payload = json.loads(response.data.decode("utf-8"))
    assert response_payload["access_token"] == token_payload["access_token"]


def test_refresh_token_sso_invalid_token(my_service, request_factory):
    user = USERS["bob@example.com"]
    # ensure user "exists" in keycloak
    my_service.keycloak.token(code=user.email)

    request = request_factory(json={"token": "keycloak_invalid__refresh_token"})
    response = my_service.refresh_token_sso(request)

    assert response.status_code == 401


def test_validate_token_sso(my_service, request_factory):
    user = USERS["bob@example.com"]
    token_payload = my_service.keycloak.token(code=user.email)
    access_token = token_payload["access_token"]

    request = request_factory()
    response = my_service.validate_token_sso(request, token=access_token)

    assert response.status_code == 200


def test_validate_token_sso_invalid_token(my_service, request_factory):
    user = USERS["bob@example.com"]
    _ = my_service.keycloak.token(code=user.email)

    request = request_factory()
    response = my_service.validate_token_sso(request, token="keycloak_invalid_token")

    assert response.status_code == 401


def test_logout_invalidates_refresh_token(my_service, request_factory):
    user = USERS["bob@example.com"]
    token_payload = my_service.keycloak.token(code=user.email)

    request = request_factory()
    request.cookies = {
        f"{MyService.sso_cookie_prefix}_refresh-token": token_payload["refresh_token"]
    }
    response = my_service.logout(request)

    assert response.status_code == 302
    with pytest.raises(KeycloakError):
        my_service.keycloak.refresh_token(token_payload["refresh_token"])
