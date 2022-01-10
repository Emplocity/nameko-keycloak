Changelog
=========

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
