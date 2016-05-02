=====
Adarnauth-EVE-SSO
=====

Adarnauth-EVE-SSO is a simple Django app to collect and manage
access tokens from EVE Online's Single Sign On feature.

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

3. Register an application with [EVE Developers](https://developers.eveonline.com/applications)
  - If your application requires scopes, select "CREST Access" and register
    all possible scopes your app can request. Otherwise "Authentication Only"
    will suffice.
  - Set the "Callback URL" to "https://yourdomain.com/eve_sso/callback"

4. Add SSO client settings to your project settings like this::

    EVE_SSO_CLIENT_ID = "my client id"
    EVE_SSO_CLIENT_SECRET = "my client secret"
    EVE_SSO_CALLBACK_URL = "my client callback url"

5. Run `python manage.py migrate` to create the eve_sso models.

6. Have views redirect to /eve_sso/redirect with required scopes in
   GET, separated by plus signs (+)

7. Retrieve tokens through CallbackRedirect models identified by
   request session key and exchange for character information.
