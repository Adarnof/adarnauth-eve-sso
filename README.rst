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

6. Have views redirect to /eve_sso/redirect with required scopes in
   GET, separated by plus signs (+)

7. Retrieve tokens through CallbackRedirect models identified by
   request session key and exchange for character information.


Usage in Views
----------

1. Import the decorator::

    from eve_sso.decorators import scopes_required

2. Wrap the view with the decorator, defining scopes required::

    @scopes_required('fittingsRead')

Use a list for multiple scopes::

    @scopes_required(['fittingsRead','fittingsWrite'])

3. Wrap the view with the decorator, accepting a second argument::

    @scopes_required('fittingsRead')
    def my_view(request, token):

4. Use this token in your view.


Manually Locating a Token
----------

1. Define a list of required scopes::

    REQUIRED_SCOPES = [
        'publicData',
        'characterFittingsRead',
        'characterFittingsWrite',
    ]

2. Collect a list of Scope models required::

    scope_list = [Scope.objects.get(name=s) for s in REQUIRED_SCOPES]

3. Check for tokens granting these scopes::

    tokens = AccessToken.objects.filter(user=MY_USER).filter(scopes__contains=scope_list)

Can also restrict by character::

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
        get = dict(request.GET)
        get['return'] = reverse(THIS_VIEW, *args)
        return redirect(reverse(eve_sso_redirect) + '?' + urllib.urlencode(get))
            
7. Use the token for your app.
