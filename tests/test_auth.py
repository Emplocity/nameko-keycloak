from unittest.mock import Mock

from nameko_keycloak.auth import AuthenticationService

from .models import USERS


def test_authentication_service_get_user_from_request(keycloak):
    def fetch_user(email):
        return USERS.get(email)

    user = USERS["bob@example.com"]
    token_payload = keycloak.token(code=user.email)
    access_token = token_payload["access_token"]

    request = Mock()
    request.headers = {"Authorization": f"Bearer {access_token}"}

    auth = AuthenticationService(keycloak, fetch_user)
    user_from_request = auth.get_user_from_request(request)

    assert user == user_from_request
