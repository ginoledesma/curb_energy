Getting Started
===============

To connect to the Curb REST API, you can instantiate a
:class:`curb_energy.client.RestApiClient` object passing in the required
credentials.

OAuth Tokens
------------

Before you can interact with the Curb REST API, you'll need to get a client
token and secret for your specific application. For that, you will need to
reach out to the `Curb support team`_ asking them for developer access to their
API. The defaults have been set to ``CHANGE_ME`` explicitly for this reason
-- you will be unable to proceed until getting these.

Once you have been given a client ID and token for your app, you can pass
this to the :class:`curb_energy.client.RestApiClient` along with the username
and password (or existing OAuth2 access/refresh token) to interact with the API.

.. warning::

    **Just to be clear**: the Client Token and Client Secret are DIFFERENT from
    the username, password, or access and refresh tokens. The Client
    Token/Secret is used to identify the application interacting with the
    REST API, and the access and refresh tokens are used to identify the user.

The library will automatically fetch an access token when authenticating with
a username and password. Subsequent requests to the REST API will use the
access token. As well, the refresh token is automatically used to request a new
access token when the previous access token has expired.


Runtime
-------

The client can be used as a context manager to automatically
handle logging in and cleaning-up:

.. code-block:: python

    import asyncio
    from curb_energy.client import RestApiClient

    async def main():
        async with RestApiClient(username='user',
                                 password='pass',
                                 client_id='APP_CLIENT_ID',
                                 client_token='APP_CLIENT_TOKEN') as client:
            profiles = await client.profiles()
            devices = await client.devices()

        for profile in profiles:
            print(profile)

        for device in devices:
            print(device)

    asyncio.get_event_loop().run_until_complete(main())


Or in a more traditional way:

.. code-block:: python

    import asyncio
    from curb_energy.client import RestApiClient

    async def main():
        client = RestApiClient(username='user', password='pass',
                               client_id='APP_CLIENT_ID',
                               client_token='APP_CLIENT_TOKEN')
        try:
            await client.authenticate()
            profiles = await client.profiles()
            devices = await client.devices()

            for profile in profiles:
                print(profile)

            for device in devices:
                print(device)
        finally:
            # Clean-up
            await client.session.close()

    asyncio.get_event_loop().run_until_complete(main())


.. _Authentication section: http://docs.energycurb.com/authentication.html
.. _Curb support team: http://energycurb.com/support/