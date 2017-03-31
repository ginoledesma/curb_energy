import datetime
import pytest
import vcr
from curb_energy.client import RestApiClient
from curb_energy.errors import CurbBaseException


@pytest.fixture
def config():
    return {'username': 'dummy',
            'password': 'dummy',
            }


@pytest.fixture
def client(config: dict, event_loop):
    return RestApiClient(**config, loop=event_loop)


@pytest.mark.asyncio
async def test_context_manager(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        async with client:
            assert client.auth_token


@pytest.mark.asyncio
async def test_login(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        token = await client.login()
        client.session.close()

    assert token == client.auth_token


@pytest.mark.asyncio
async def test_devices(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        async with client:
            assert await client.devices()


@pytest.mark.asyncio
async def test_profiles(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        async with client:
            assert await client.profiles()


@pytest.mark.asyncio
async def test_historical(client: RestApiClient):
    now = int(datetime.datetime.utcnow().timestamp())
    # Ignore the URI params for now
    with vcr.use_cassette('success.yaml', match_on=['host', 'port', 'path']):
        async with client:
            assert await client.historical_data(profile_id=5050, until=now)


@pytest.mark.asyncio
async def test_login_failed(client: RestApiClient):
    with vcr.use_cassette('unauthorized.yaml', match_on=['host', 'port']):
        with pytest.raises(CurbBaseException):
            async with client:
                pass


@pytest.mark.asyncio
async def test_unauthorized(client: RestApiClient):
    with vcr.use_cassette('unauthorized.yaml', match_on=['host', 'port']):
        with pytest.raises(CurbBaseException):
            assert not await client.login()

        assert not await client.fetch_access_token()
        assert not await client.fetch_access_token(username='other',
                                                   password='other')

        await client.session.close()

        assert not client.auth_token


@pytest.mark.asyncio
async def test_non_json_responses(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        async with client:
            assert await client.historical_data(profile_id=-1) is None
