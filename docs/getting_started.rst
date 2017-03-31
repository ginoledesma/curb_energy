Getting Started
===============

To connect to the Curb REST API, you can instantiate a
:class:`curb_energy.client.RestApiClient` object passing in the required
credentials. The client can be used as a context manager to automatically
handle logging in and cleaning-up:

.. code-block:: python

    import asyncio
    from curb_energy.client import RestApiClient

    async def main():
        async with RestApiClient(username='user', password='pass') as client:
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
        client = RestApiClient(username='user', password='pass')
        try:
            await client.login()
            profiles = await client.profiles()
            devices = await client.devices()

            for profile in profiles:
                print(profile)

            for device in devices:
                print(device)
        finally:
            await client.session.close()

    asyncio.get_event_loop().run_until_complete(main())
