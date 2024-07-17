from nameko_keycloak.auth import AuthenticationService

from .models import USERS


def fetch_user(email, token_payload):
    return USERS.get(email)


def test_authentication_service_get_user_from_request_cookie(keycloak, request_factory):
    user = USERS["bob@example.com"]
    token_payload = keycloak.token(code=user.email)

    request = request_factory()
    prefix = "my-app"
    request.cookies = {f"{prefix}_access-token": token_payload["access_token"]}

    auth = AuthenticationService(keycloak, fetch_user, sso_cookie_prefix=prefix)
    user_from_request = auth.get_user_from_request(request)

    assert user == user_from_request


def test_authentication_service_get_user_from_request_authorization_header(
    keycloak, request_factory
):
    user = USERS["bob@example.com"]
    token_payload = keycloak.token(code=user.email)
    access_token = token_payload["access_token"]

    request = request_factory()
    request.headers = {"Authorization": f"Bearer {access_token}"}

    auth = AuthenticationService(keycloak, fetch_user)
    user_from_request = auth.get_user_from_request(request)

    assert user == user_from_request


def test_authentication_service_get_user_from_request_anonymous(
    keycloak, request_factory
):
    request = request_factory()

    auth = AuthenticationService(keycloak, fetch_user)
    user_from_request = auth.get_user_from_request(request)

    assert user_from_request is None


def test_authentication_service_get_token_payload(keycloak):
    user = USERS["bob@example.com"]
    token_payload = keycloak.token(code=user.email)
    access_token = token_payload["access_token"]

    auth = AuthenticationService(keycloak, fetch_user)
    decoded_payload = auth.get_token_payload(access_token)

    assert decoded_payload["email"] == user.email


def test_authentication_service_get_token_payload_invalid(keycloak):
    auth = AuthenticationService(keycloak, fetch_user)
    access_token = "invalid"

    decoded_payload = auth.get_token_payload(access_token)

    assert decoded_payload == {}
