from unittest.mock import Mock

from nameko_keycloak.auth import AuthenticationService


def test_authentication_service_get_user_from_request(keycloak, users):
    def fetch_user(email):
        return users.get(email)

    user = users["bob@example.com"]
    token_payload = keycloak.token(code=user.email)
    access_token = token_payload["access_token"]

    request = Mock()
    request.headers = {"Authorization": f"Bearer {access_token}"}

    auth = AuthenticationService(keycloak, fetch_user)
    user_from_request = auth.get_user_from_request(request)

    assert user == user_from_request
