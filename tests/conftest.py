from dataclasses import dataclass

import pytest

from nameko_keycloak.auth import AuthenticationService
from nameko_keycloak.fakes import FakeKeycloak


@dataclass
class User:
    email: str


@pytest.fixture
def users():
    return {
        u.email: u
        for u in [User(email="bob@example.com"), User(email="doug@example.com")]
    }


@pytest.fixture
def keycloak():
    return FakeKeycloak()


@pytest.fixture
def authentication_service(keycloak, users):
    def _fetch_user(email):
        return users.get(email)

    return AuthenticationService(keycloak, _fetch_user)
