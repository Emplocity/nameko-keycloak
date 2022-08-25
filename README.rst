.. include-section-overview-start

===============
nameko-keycloak
===============

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |actions|
        | |coveralls|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/nameko-keycloak/badge/?style=flat
    :target: https://readthedocs.org/projects/nameko-keycloak
    :alt: Documentation Status

.. |actions| image:: https://github.com/Emplocity/nameko-keycloak/actions/workflows/build.yml/badge.svg
    :alt: Github Actions Build Status
    :target: https://github.com/Emplocity/nameko-keycloak/actions/

.. |coveralls| image:: https://coveralls.io/repos/Emplocity/nameko-keycloak/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/Emplocity/nameko-keycloak

.. |version| image:: https://img.shields.io/pypi/v/nameko-keycloak.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/nameko-keycloak

.. |wheel| image:: https://img.shields.io/pypi/wheel/nameko-keycloak.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/nameko-keycloak

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/nameko-keycloak.svg
    :alt: Supported versions
    :target: https://pypi.org/project/nameko-keycloak

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/nameko-keycloak.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/nameko-keycloak

.. |commits-since| image:: https://img.shields.io/github/commits-since/Emplocity/nameko-keycloak/v0.6.0.svg
    :alt: Commits since latest release
    :target: https://github.com/Emplocity/nameko-keycloak/compare/v0.6.0...master

.. end-badges


**This package is still work in progress.**

Helpers to integrate Single Sign-On in nameko_-based applications using Keycloak_.

.. _nameko: https://www.nameko.io/
.. _Keycloak: https://www.keycloak.org/

Features
========

 - nameko service mixin
 - database and model-agnostic user management
 - authentication service
 - fake Keycloak client for use in tests

Installation
============

::

    pip install nameko-keycloak

You can also install the in-development version with::

    pip install https://github.com/emplocity/nameko-keycloak/archive/master.zip

.. include-section-overview-end

Usage
=====

.. include-section-usage-start

To set up SSO with Keycloak in your nameko service, follow these steps.

1. Get Keycloak configuration from realm -> Clients -> Installation, download
   as Keycloak OIDC JSON.

   .. note::
      Make sure ``auth-server-url`` ends with a trailing slash.

   Save this configuration in a .json file.
2. Add the mixin and dependency provider to your service and point to OIDC
   JSON config::

       from nameko_keycloak.dependencies import KeycloakProvider
       from nameko_keycloak.service import KeycloakSsoServiceMixin

       class MyService(KeycloakSsoServiceMixin):
           keycloak = KeycloakProvider("/tmp/keycloak.json")

3. Set up URLs for HTTP endpoints. The mixin exposes five methods prefixed
   with ``keycloak_``, which you should use in your HTTP service.
   Delegate from your entrypoints like this::

        @http("GET", "/login")
        def login_sso(self, request):
            return self.keycloak_login_sso(request)

   This way it is up to you to control the URL routes and any middleware
   or extra request handling (such as CORS headers).
4. Implement a ``fetch_user()`` method on your service that takes user's
   email address as a single argument and returns a user instance for that
   email (or ``None`` if no such user exists in whatever storage you're using).

   .. note::
      We assume that email address is unique for every user.

   For example::

        def fetch_user(self, email: str) -> Optional[User]:
            user_manager = UserManager(self.db.session)
            return user_manager.get_by_email(email)

   This method is used to ensure that there is a local application user who
   matches the global identity stored in Keycloak.

5. (Optionally) Implement success and failure hook methods on your service.

   If you provide ``keycloak_success()`` method, the mixin will call it after
   successful login and redirect from Keycloak back to your application.
   The method will receive currently logged user as its argument. Similarly
   the mixin will call ``keycloak_failure()`` upon Keycloak errors.

   Example::

        def keycloak_success(self, user: User) -> None:
            logger.info(f"Successful login: {user=}")

        def keycloak_failure(self) -> None:
            logger.error("Failed to log in")

   .. note::
      Failure hooks execute in a try/except block, so you can access
      ``sys.exc_info``, for example to capture exception to Sentry or other
      error reporting tool.

.. include-section-usage-end

Documentation
=============

https://nameko-keycloak.readthedocs.io/


Authors
=======

``nameko-keycloak`` is developed and maintained by `Emplocity`_.

.. _Emplocity: https://emplocity.com/


License
=======

This work is released under the Apache 2.0 license.
