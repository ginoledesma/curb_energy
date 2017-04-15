import datetime
import pytest
import vcr
from curb_energy.client import AuthToken
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
async def test_context_manager_without_token(client: RestApiClient):
    """
    When used as a context manager without an existing token, the API client
    should attempt to authenticate and fetch an access token.
    """
    with vcr.use_cassette('success.yaml'):
        assert client.auth_token is None
        async with client:
            assert client.auth_token and client.auth_token.is_valid


@pytest.mark.asyncio
async def test_context_manager_with_token(config):
    token = AuthToken(access_token='change_me',
                      refresh_token='change_me',
                      expires_in=300,
                      user_id=1)
    assert token.is_valid

    with vcr.use_cassette('success.yaml'):
        async with RestApiClient(auth_token=token, **config) as client:
            assert client.auth_token == token


@pytest.mark.asyncio
async def test_context_manager_with_expired_token(config):
    token = AuthToken(access_token='change_me',
                      refresh_token='change_me',
                      # expired 5 minutes ago
                      expires_in=-300,
                      user_id=1)
    assert not token.is_valid

    with vcr.use_cassette('success.yaml'):
        async with RestApiClient(auth_token=token, **config) as client:
            assert client.auth_token != token
            assert client.auth_token.is_valid


@pytest.mark.asyncio
async def test_authenticate(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        token = await client.authenticate()
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
async def test_implicit_entrypoint_loading(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        client._entry_point = None
        assert await client.devices()
        assert client._entry_point

    # Reload the cassette for playback
    with vcr.use_cassette('success.yaml'):
        client._entry_point = None
        assert await client.profiles()
        assert client._entry_point

    await client.session.close()


@pytest.mark.asyncio
async def test_historical(client: RestApiClient):
    now = int(datetime.datetime.utcnow().timestamp())
    # Ignore the URI params for now
    with vcr.use_cassette('success.yaml', match_on=['host', 'port', 'path']):
        async with client:
            assert await client.historical_data(profile_id=5050, until=now)


@pytest.mark.asyncio
async def test_authenticate_failed(client: RestApiClient):
    with vcr.use_cassette('unauthorized.yaml', match_on=['host', 'port']):
        with pytest.raises(CurbBaseException):
            async with client:
                pass


@pytest.mark.asyncio
async def test_unauthorized(client: RestApiClient):
    with vcr.use_cassette('unauthorized.yaml', match_on=['host', 'port']):
        with pytest.raises(CurbBaseException):
            assert not await client.authenticate()

        assert not await client.fetch_access_token()
        assert not await client.fetch_access_token(username='other',
                                                   password='other')

        assert not client.auth_token

        with pytest.raises(CurbBaseException):
            await client.refresh_access_token()

        bogus = AuthToken(user_id=100, expires_in=300, access_token="a",
                          refresh_token="b")
        client._auth_token = bogus
        assert not await client.refresh_access_token()

        await client.session.close()


@pytest.mark.asyncio
async def test_non_json_responses(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        async with client:
            assert await client.historical_data(profile_id=-1) is None


@pytest.mark.asyncio
async def test_refresh_auth_token(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        async with client:
            old_token = client.auth_token

            # refresh_access_token updates the auth token property
            new_token = await client.refresh_access_token()
            assert new_token == client.auth_token
            assert new_token is client.auth_token

            assert new_token.user_id == old_token.user_id
            assert new_token.expiry > old_token.expiry


@pytest.mark.asyncio
async def test_refresh_expired_token_before_request(client: RestApiClient):
    with vcr.use_cassette('success.yaml'):
        async with client:
            # Force the token to be expired
            old_token = client.auth_token
            old_token.expires_in = -300

            assert client.auth_token is old_token
            assert not client.auth_token.is_valid

            # Attempt to make request using expired token; this should
            # automatically fetch a new one
            profiles = await client.profiles()
            assert profiles

            # Verify we do have a new token
            assert client.auth_token.is_valid
            assert old_token is not client.auth_token
            assert old_token.expiry < client.auth_token.expiry
