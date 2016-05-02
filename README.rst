=====
Adarnauth-EVE-SSO
=====

Adarnauth-EVE-SSO is a simple Django app to collect and manage
access tokens from EVE Online's Single-SignOn feature.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "eve_sso" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'eve_sso',
    ]

2. Include the eve_sso URLconf in your project urls.py like this::

    url(r'^eve_sso/', include('eve_sso.urls')),

3. Run `python manage.py migrate` to create the eve_sso models.

4. Have views redirect to /eve_sso/redirect with required scopes in
   GET, separated by plus signs (+)

5. Retrieve tokens through CallbackRedirect models identified by
   request session key and exchange for character information.
