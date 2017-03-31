import json
import pytest
from unittest.mock import MagicMock
from curb_energy.client import RealTimeClient
from curb_energy.models import RealTimeConfig


@pytest.fixture
def config():
    return RealTimeConfig(ws_url='wss://username:password@localhost:8443',
                          topic='curb/abcdefgh/active',
                          prefix='urn:energycurb:registers:curb:abcdefgh',
                          format='curb')


@pytest.fixture
def driver():
    CONNECTED = 0x0

    class Dummy(object):
        def __init__(self):
            self.mocked = MagicMock()

        async def connect(self, *args, **kwargs):
            self.mocked.connect(*args, **kwargs)
            return CONNECTED

        async def disconnect(self, *args, **kwargs):
            self.mocked.disconnect(*args, **kwargs)

        async def subscribe(self, *args, **kwargs):
            self.mocked.subscribe(*args, **kwargs)

        async def unsubscribe(self, *args, **kwargs):
            self.mocked.unsubscribe(*args, **kwargs)

        async def deliver_message(self):
            return self.mocked.deliver_message()

    return Dummy


@pytest.fixture
def client(config, driver):
    return RealTimeClient(config=config, driver=driver)


@pytest.mark.asyncio
async def test_context_manager(driver, config):
    async with RealTimeClient(config=config, driver=driver) as client:
        assert client.is_connected

    assert not client.is_connected


@pytest.mark.asyncio
async def test_read(client):
    payload = MagicMock(data=json.dumps({'ts': 1, 'measurements': {}}))
    packet = MagicMock(payload=payload)
    message = MagicMock(publish_packet=packet)

    client.driver.mocked.deliver_message.return_value = message
    assert await client.read()


@pytest.mark.asyncio
async def test_read_error(client):
    payload = MagicMock(data='not a valid json string')
    packet = MagicMock(payload=payload)
    message = MagicMock(publish_packet=packet)

    client.driver.mocked.deliver_message.return_value = message
    assert not await client.read()
