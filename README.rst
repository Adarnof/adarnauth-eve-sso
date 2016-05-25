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

3. Register an application with the EVE Developers site at
   https://developers.eveonline.com/applications
  - If your application requires scopes, select "CREST Access" and register
    all possible scopes your app can request. Otherwise "Authentication Only"
    will suffice.
  - Set the "Callback URL" to "https://yourdomain.com/eve_sso/callback"

4. Add SSO client settings to your project settings like this::

    EVE_SSO_CLIENT_ID = "my client id"
    EVE_SSO_CLIENT_SECRET = "my client secret"
    EVE_SSO_CALLBACK_URL = "my client callback url"

5. Run `python manage.py migrate` to create the eve_sso models.

Usage in Views
----------

1. To find tokens on file for the user with specific scopes, or redirect to
create a new one if none found::

    from eve_sso.decorators import token_required
    @token_required(['characterFiittingsRead', 'characterFittingsWrite'])
    def my_view(request, tokens):
        ...stuff...

2. To request a new access token from SSO, add the new argument::

    from eve_sso.decorators import token_required
    @token_required(scopes=['publicData'], new=True)
    def my_view(request, tokens):
        ...stuff...

3. Filter for the token you want to use in your view::

    my_character_tokens = tokens.filter(character_id=MY_CHARACTER_ID)


Manually Locating a Token
----------

1. Define a list of required scopes::

    REQUIRED_SCOPES = [
        'publicData',
        'characterFittingsRead',
        'characterFittingsWrite',
    ]

3. Check for tokens granting these scopes::

    tokens = AccessToken.objects.filter(user=MY_USER).filter(scopes__name__in=REQUIRED_SCOPES)

4. Can also restrict by character::

    tokens = AccessToken.objects.filter(character_id=MY_CHARACTER_ID)

5. Loop through existing tokens, checking if still valid::

    for t in tokens:
        try:
            token = t.token
            break
        except TokenExpiredError:
            t.delete()
        except TokenInvalidError:
            t.delete()

6. If no valid tokens found, redirect to SSO::

    else:
        return sso_redirect(request, scopes=REQUIRED_SCOPES)
            
7. Use the token for your app.
