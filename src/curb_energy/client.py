"""
Client module for interacting with the Curb REST and Real-Time APIs
"""

import aiohttp
import asyncio
import base64
import certifi
import curb_energy
import json
import logging
import pytz
import ssl
import sys
from collections import namedtuple
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from datetime import datetime
from datetime import timedelta
from curb_energy import schema
from curb_energy import models
from curb_energy.errors import CurbBaseException
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.connack import CONNECTION_ACCEPTED
from hbmqtt.client import QOS_0
from hbmqtt.errors import MQTTException


__all__ = [
    'AuthToken',
    'RestApiClient',
    'RealTimeClient',
    'RealTimeMessage',
]

logger = logging.getLogger(__name__)


# You will need to obtain an OAuth client token for your specific application
# See <http://docs.energycurb.com/authentication.html> for info on obtaining one
OAUTH_CLIENT_TOKEN = "CHANGE_ME"
OAUTH_CLIENT_SECRET = "CHANGE_ME"


def now() -> datetime:
    """
    Helper function to return current date/time in UTC    

    :rtype: datetime.datetime
    """
    return datetime.now(pytz.utc)


class AuthToken(object):
    """
    Curb API OAuth2 Token. For more information, refer to: 
    <https://oauth.net/articles/authentication/>
    """
    def __init__(self,
                 access_token: str=None,
                 refresh_token: str=None,
                 expires_in: int=0,
                 user_id: int=0,
                 token_type: str='bearer'):
        """
        Create an :class:`AuthToken` instance.

        :param access_token: The access token 
        :param refresh_token: The refresh token  
        :param expires_in: The time, in seconds, this token is valid for. 
        :param user_id: The unique ID of the user associated with this token
        :param token_type: Bearer type 
        """
        self.generated_on = now()
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
        self.user_id = user_id
        self.token_type = token_type

    @property
    def expiry(self) -> datetime:
        """
        The expiration date of the token (in UTC)

        :return: Expiry date (in UTC)
        :rtype: datetime.datetime
        """
        return self.generated_on + timedelta(0, self.expires_in)

    @property
    def is_valid(self) -> bool:
        return self.access_token and self.refresh_token and now() < self.expiry

    @staticmethod
    def from_json(data: str) -> 'AuthToken':
        """
        Creates an AuthToken object from the given JSON payload.

        :param data: Token data
        :return: Creates an AuthToken instance from the given payload
        :raises: :class:`ValueError`
        """
        d = json.loads(data)
        return AuthToken(access_token=d.get('access_token'),
                         refresh_token=d.get('refresh_token'),
                         expires_in=d.get('expires_in'),
                         user_id=d.get('user_id'),
                         token_type=d.get('token_type'),
                         )

    def json(self) -> str:
        """
        Serializes the AuthToken into JSON

        :return: JSON version of the AuthToken
        """
        return json.dumps(
            dict(access_token=self.access_token,
                 refresh_token=self.refresh_token,
                 expires_in=(self.expiry - now()).total_seconds(),
                 user_id=self.user_id,
                 token_type=self.token_type,
                 )
        )

    def __repr__(self): # pragma: no cover
        return self.json()

    def __eq__(self, other: 'AuthToken'):
        if not isinstance(other, AuthToken):
            return NotImplemented

        # The expiration period of a token can be ignored
        attrs = ['access_token', 'refresh_token', 'user_id', 'token_type']
        return all([getattr(self, a) == getattr(other, a) for a in attrs])

    def __ne__(self, other: 'AuthToken'):
        if not isinstance(other, AuthToken):
            return NotImplemented

        # The expiration period of a token can be ignored
        attrs = ['access_token', 'refresh_token', 'user_id', 'token_type']
        return any([getattr(self, a) != getattr(other, a) for a in attrs])


RealTimeMessage = namedtuple('RealTimeMessage', ['timestamp', 'measurements'])


class RealTimeClient(object):
    """
    A client to the Curb Energy Real-Time Streaming API
    
    .. todo::
    
        Refactor to support different access mechanisms. For now, 
        we're limited to using MQTT over WebSockets
    """

    def __init__(self, config: models.RealTimeConfig,
                 driver: Callable=MQTTClient):
        """
        Create an instance of :class:`RealTimeClient`.

        :param config: Real Time Config
        :param driver: Real Time client driver
        
        Example:
        
        .. code-block:: python
        
            client = RealTimeClient(config)
            await client.connect()
            while condition:
                data = await client.stream()
            await client.disconnect()
            
        Used as a context manager:            

        .. code-block:: python
        
            async with RealTimeClient(config) as client:
                while condition:
                    data = await client.stream()        
        """
        self._config = config
        self._connected = False
        self._impl = driver()
        self._streaming = False

    async def connect(self):
        """
        Connect to the Real-time API
        """

        # FIXME: HBMQTT + ssl_context for consistency?
        connect_kwargs = {}
        if self.config.url.startswith(('wss', 'https')):
            connect_kwargs['cafile'] = certifi.where()

        rc = await self._impl.connect(uri=self.config.url, **connect_kwargs)
        self._connected = rc == CONNECTION_ACCEPTED

        await self._impl.subscribe([(self.config.topic, QOS_0)])

    async def disconnect(self):
        """
        Disconnect from the Real-time API
        """

        self._connected = False
        await self._impl.unsubscribe(self.config.topic)
        await self._impl.disconnect()

    @property
    def config(self) -> models.RealTimeConfig:
        """
        Returns the configuration parameters for the client.
        """
        return self._config

    @property
    def driver(self):
        return self._impl

    @property
    def is_connected(self) -> bool:
        """
        Returns True if the real-time client has successfully established a 
        connection with the Real-Time API, False otherwise.
        """
        return self._connected

    async def __aenter__(self):
        """
        When used as a context-manager, the client automatically connects to 
        the real-time API.
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        When used as a context-manager, the client automatically disconnects 
        from the real-time API.
        """
        if self.is_connected:
            await self.disconnect()

    async def read(self) -> RealTimeMessage:
        """
        Returns a single stream from the real-time API, or None when an
        error occurs. This may raise a :class:`ValueError` when the returned 
        data is invalid JSON. 
        
        :returns: Returns measurements
        :raises: :class:`ValueError`
        """
        self._streaming = True
        try:
            message = await self._impl.deliver_message()
            """ :type: hbmqtt.session.ApplicationMessage """

            packet = message.publish_packet
            """ :type: hbmqtt.mqtt.publish.PublishPacket """

            logger.debug("{} => {}".format(
                packet.variable_header.topic_name,
                packet.payload.data)
            )

            decoded = json.loads(packet.payload.data)
            return RealTimeMessage(timestamp=decoded['ts'],
                                   measurements=decoded['measurements'])
        except (MQTTException, json.decoder.JSONDecodeError, KeyError) as err:
            logger.warning("Error reading packet: {}".format(err))


class RestApiClient(object):
    """
    A client for the `Curb REST API <http://docs.energycurb.com/>`_
    """
    API_URL = "https://app.energycurb.com"
    USER_AGENT = 'CurbEnergy-RestApiClient/' + curb_energy.__version__

    # Convenience labels
    PER_DAY = '1D'
    PER_HOUR = '1H'
    PER_MIN = '1T'

    WATT = 'w'
    DOLLAR_PER_HOUR = '$/hr'

    def __init__(self,
                 loop: asyncio.AbstractEventLoop = None,
                 username: str = None,
                 password: str = None,
                 auth_token: AuthToken = None,
                 api_url: str = API_URL,
                 client_token: str = OAUTH_CLIENT_TOKEN,
                 client_secret: str = OAUTH_CLIENT_SECRET,
                 ssl_context: ssl.SSLContext = None):
        """
        Initialize the REST API client.

        The Curb API uses Oauth2 authentication. An access token can be fetched
        by supplying a valid username and password as credentials. Subsequent
        authentication with the API will be done using the Oauth2 token in 
        the form of :class:`~curb_energy.client.AuthToken`.
        
        You can also pass an existing token instead of a username/password.

        :param username: Username
        :param password: Password
        :param auth_token: Oauth2 client token
        :param api_url: The URL to the Curb REST API
        :param client_token: The application client token (app identifier)
        :param client_secret: The application client secret (app password)
        :param ssl_context: Optional SSL

        .. warning::
        
            As a client to the Curb REST API, you **MUST** provide your own 
            client_token and client_secret which identifies the *APPLICATION* 
            you are developing. This is separate from the username/password 
            or access token that identifies the *USER* accessing their data.
            
            See <http://docs.energycurb.com/authentication.html> for more info.
            You'll need to contact the Curb Support Team at 
            <http://energycurb.com/support/> for assistance.
        
        Example:
        
        .. code-block:: python
        
            async with RestApiClient(username=user,
                                     password=pass, 
                                     client_token='CHANGE_ME', 
                                     client_secret='CHANGE_ME') as client:
                profiles = await client.profiles()
                devices = await client.devices()

                for profile in profiles:
                    print(profile)
        
                for device in devices:
                    print(device)

        Or more traditionally:
        
        .. code-block:: python

            client = RestApiClient(username=user,
                                   password=pass, 
                                   client_token='CHANGE_ME',
                                   client_secret='CHANGE_ME')
            try:
                # Fetch and set the access token
                await client.authenticate()
                
                # code goes here
                
            finally:
                await client.session.close()            

        """
        self.api_url = api_url
        self.auth_username = username
        self.auth_password = password
        self.client_token = client_token
        self.client_secret = client_secret
        self._auth_token = auth_token
        self._loop = loop
        self._entry_point = None

        conn = aiohttp.TCPConnector(ssl_context=ssl_context)
        h = {'User-Agent': self.USER_AGENT}
        self._session = aiohttp.ClientSession(connector=conn, headers=h)

    def _auth_headers(self) -> Dict:
        """
        Helper function to return HTTP headers for the REST API
        
        :return: HTTP authorization headers
        """
        encoded = base64.b64encode(self.auth_token.access_token.encode())
        return {
            'Authorization': 'Bearer {}'.format(encoded.decode('latin1'))
        }

    def _make_url(self, path: str) -> str:
        """
        Helper function to create URIs for the REST API 

        :param path: The path to append to the base API prefix
        """
        return "{}{}".format(self.api_url, path)

    @property
    def auth_token(self) -> AuthToken:
        """
        The AuthToken associated with the REST API session        

        :return: The AuthToken associated with the session
        """
        return self._auth_token

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session

    async def authenticate(self) -> AuthToken:
        """
        Authenticates with the REST API by fetching an access token, raising 
        an exception on failure. The access token is stored as a property. 
        This method is automatically called when the client is used as a 
        context manager.

        :returns: The authentication token
        :raises: :class:`~curb_energy.errors.CurbBaseException`
        """
        token = self._auth_token
        if token is None:
            token = await self.fetch_access_token()

        elif not token.is_valid:
            token = await self.refresh_access_token()

        if not (token and token.is_valid):
            raise CurbBaseException("Authentication Error")

        self._auth_token = token
        return self.auth_token

    async def fetch_access_token(self,
                                 client_token: str=None,
                                 client_secret: str=None,
                                 username: str=None,
                                 password: str=None) -> Optional[AuthToken]:
        """
        Fetches an access token using the given credentials. The supplied 
        parameters override the original credentials passed to instance of 
        the REST API client.
        
        :param client_token: The OAuth Client Token (app identifier)
        :param client_secret: The OAuth Client Secret (app password)
        :param username: The username to authenticate with
        :param password: The password to authenticate with
        :returns: Returns the access token after authentication
        """
        url = self._make_url("/oauth2/token")

        payload = {
            'grant_type': 'password',
            'username': username or self.auth_username,
            'password': password or self.auth_password,
        }

        _token = client_token if client_token else self.client_token
        _secret = client_secret if client_secret else self.client_secret

        auth = aiohttp.BasicAuth(_token, password=_secret)
        async with self._session.post(url, data=payload, auth=auth) as response:
            if response.status != 200:
                logger.warning("Unsuccessful request: {}".format(response.text))
                return

        return AuthToken(**await response.json())

    async def refresh_access_token(self) -> AuthToken:
        """
        Get a new access token using an existing refresh token and associated 
        user ID. All other access tokens are immediately invalidated. When 
        calling this method, 
        :attr:`~curb_energy.client.RestApiClient.auth_token` is automatically 
        set to the new token. 

        :return: a new access token
        :raises: :class:`~curb_energy.errors.CurbBaseException` when 
                 :attr:`~curb_energy.client.RestApiClient.auth_token` is not set
        """
        if self.auth_token is None:
            raise CurbBaseException("No existing auth token")

        url = self._make_url("/oauth2/token")

        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.auth_token.refresh_token,
            'user_id': self.auth_token.user_id,
        }

        auth = aiohttp.BasicAuth(self.client_token, password=self.client_secret)
        async with self._session.post(url, data=payload, auth=auth) as response:
            if response.status != 200:
                logger.warning("Unsuccessful request: {}".format(response.text))
                return

        token = AuthToken(**await response.json())

        # Refreshing tokens automatically invalidates older tokens, requiring
        # us to use the new token effective immediately.
        self._auth_token = token
        return token

    async def entry_point(self) -> Dict:
        """
        Return the resources the authenticated user has access to, namely 
        Profiles and Devices. This is automatically called when the client is
        used as a context manager.
        
        :return: a dict of links to the Profiles and Devices 
        """
        self._entry_point = await self._fetch(schema.EntryPointSchema,
                                              self._make_url("/api"))
        return self._entry_point

    async def profiles(self) -> List[models.Profile]:
        """
        Return a list of profiles associated with the authenticated user.
        
        :returns: A list of profiles
        """
        if not self._entry_point:
            await self.entry_point()

        url = self._make_url(self._entry_point['profiles']['href'])
        return await self._fetch(schema.ProfilesSchema, url)

    async def devices(self) -> List[models.Device]:
        """
        Return a list of devices associated with the authenticated user

        :returns: A list of devices
        """
        if not self._entry_point:
            await self.entry_point()

        url = self._make_url(self._entry_point['devices']['href'])
        container = await self._fetch(schema.DevicesSchema, url)
        return container['devices']

    async def historical_data(self,
                              profile_id: int=0,
                              granularity: str=PER_HOUR,
                              unit: str=DOLLAR_PER_HOUR,
                              since: int=0,
                              until: int=None) -> models.Measurement:
        """
        Return all recorded measurements for the given profile.

        :param profile_id: The profile configuration 
        :param granularity: Per Minute, Per Hour (default), or Per Day 
        :param unit: Dollars Per Hour, or Watts (default) 
        :param since: Start time of measurements (in epoch format). Use 0 to
                      indicate the beginning, which is the default. 
        :param until: End time of measurements (in epoch format) 
        """
        url = self._make_url('/api/profiles/%d/historical-data' % profile_id)
        params = dict(granularity=granularity, unit=unit, since=since)

        if until is not None:
            params['until'] = until

        return await self._fetch(schema.HistoricalData, url, params=params)

    async def __aenter__(self):
        """
        Automatically fetch an access token when used as a context-manager if
        no access token was provided (or if it is already expired)
        """
        if self.auth_token and self.auth_token.is_valid:
            return self

        try:
            await self.authenticate()
            await self.entry_point()
        except:
            await self.__aexit__(*sys.exc_info())
            raise
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Automatically disconnect when used as a context-manager
        """
        if not self._session.closed:
            await self._session.close()

    async def _fetch(self, schema_class: schema.BaseSchema,
                     url: str,
                     params: dict=None) -> Optional[models.BaseModel]:
        """
        Helper function to fetch the REST resource of type schema_class at 
        the given URL
        
        :param schema_class: Schema
        :param url: The URL of the REST resource
        :param params: URL query parameters 
        :return: An instance of the REST resource        
        :raises: IOError
        """
        # Refresh our access token if it's expired
        if not (self.auth_token and self.auth_token.is_valid):
            await self.authenticate()

        async with self._session.get(url,
                                     headers=self._auth_headers(),
                                     params=params) as response:
            logger.info(response.text)
            try:
                data = await response.json()
            except json.decoder.JSONDecodeError as err:
                logger.warning('Invalid JSON: {}'.format(err))
                return None

            return schema_class().load(data).data
