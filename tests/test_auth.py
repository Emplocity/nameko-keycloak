from unittest.mock import Mock

from nameko_keycloak.auth import AuthenticationService

from .models import USERS


def fetch_user(email, token_payload):
    return USERS.get(email)


def test_authentication_service_get_user_from_request(keycloak):

    user = USERS["bob@example.com"]
    token_payload = keycloak.token(code=user.email)
    access_token = token_payload["access_token"]

    request = Mock()
    request.headers = {"Authorization": f"Bearer {access_token}"}

    auth = AuthenticationService(keycloak, fetch_user)
    user_from_request = auth.get_user_from_request(request)

    assert user == user_from_request


def test_authentication_service_get_user_from_request_anonymous(keycloak):
    request = Mock()
    request.headers = {}

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
