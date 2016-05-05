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

1. Define a list of required scopes::

    REQUIRED_SCOPES = [
        'publicData',
        'characterFittingsRead',
        'characterFittingsWrite',
    ]

2. Collect a list of Scope models required::

    scope_list = [Scope.objects.get(name=s) for s in REQUIRED_SCOPES]

3. Check if this is a SSO redirect::

    try:
        callback = CallbackRedirect.objects.get_by_request(request)
        if callback.token:
            callback.token.exchange()
    except CallbackRedirect.DoesNotExist:
        pass

4. Check for tokens granting these scopes::

    token_datas = TokenData.objects.filter(token__user=USER).filter(scopes__in=scope_list)
    tokens = [t.token for t in token_datas]

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
        get = request.GET
        get['return'] = reverse(THIS_VIEW, *args)
        return redirect(reverse(eve_sso_redirect) + '?' + urllib.urlencode(get))
            
7. Use the token for your app.
