Changelog
=========

2.1.0 (2025-05-14)
------------------

* Add support for Python 3.11, 3.12 and 3.13.
* Decrease log level when an access token naturally expires, this is not an
  exceptional situation.

2.0.0 (2024-07-19)
------------------

* [Likely breaking change] Upgrade python-keycloak to 4.x and switch from
  python-jose to jwcrypto. If you rely on catching exceptions from the
  underlying JWT library yourself, you need to update that code.
* Don't engage failure hook when refresh token expires. This is a legitimate
  use case and not an error.

1.0.0 (2024-02-13)
------------------

* [Breaking change] Switch to HttpOnly cookies. This means that frontend
  apps can no longer access the tokens.
* Drop support for Python 3.8.

0.7.0 (2022-10-13)
------------------

* Building package with pyproject.toml

0.6.1 (2022-10-13)
------------------

* Relax upper bounds on python-keycloak.

0.6.0 (2022-08-24)
------------------

* Add support for nameko 3.0 RC.

0.5.0 (2022-04-12)
------------------

* Add Secure=true flag to all cookies. This requires serving over HTTPS only,
  but you should be doing that already if you care about security.

0.4.0 (2022-02-03)
------------------

* [Breaking change] ``fetch_user`` callback now takes two arguments: email
  and token payload. This allows the clients to augment their User instances
  with arbitrary data encoded in the token.

0.3.0 (2022-01-10)
------------------

* [Breaking change] ``get_token_from_request`` now returns ``Optional[Token]``.
  This fixes a KeyError in ``AuthenticationService``, but it is technically
  a breaking change since ``get_token_from_request`` could be used on its own.

0.2.0 (2021-12-28)
------------------

* Expand usage documentation.

0.1.2 (2021-11-12)
------------------

* Add support for Werkzeug 2.0.

0.1.1 (2021-10-15)
------------------

* Add py.typed to mark package as PEP561-compatible.

0.1 (2021-09-02)
----------------

* First release on PyPI.
