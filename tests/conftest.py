from json import dumps
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from werkzeug.datastructures import MultiDict
from werkzeug.wrappers import Request

from nameko_keycloak.auth import AuthenticationService
from nameko_keycloak.fakes import FakeKeycloak

from .models import USERS


@pytest.fixture
def keycloak():
    return FakeKeycloak()


@pytest.fixture
def authentication_service(keycloak):
    def _fetch_user(email):
        return USERS.get(email)

    return AuthenticationService(keycloak, _fetch_user)


class RequestFactory:
    def __call__(
        self,
        method: str = "GET",
        form: Dict[str, Any] = None,
        json: Any = None,
        args: Dict[str, Any] = None,
    ) -> Request:
        request = MagicMock(spec=Request)
        request.method = method
        request.args = {} if args is None else args
        request.headers = {}
        if form is not None:
            request.mimetype = "application/form-data"
            request.form = MultiDict(form)
        elif json is not None:
            request.mimetype = "application/json"
            request.data = dumps(json).encode("utf-8")
        request.get_data = MagicMock(return_value=request.data)
        request.user_agent.string = "request_factory"
        request.access_route = ["127.0.0.1"]
        request.referrer = ""
        return request


@pytest.fixture
def request_factory():
    return RequestFactory()
