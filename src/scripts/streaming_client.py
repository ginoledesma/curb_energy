import argparse
import asyncio
import logging
import os
import signal
import textwrap
from curb_energy.client import AuthToken
from curb_energy.client import RealTimeClient
from curb_energy.client import RestApiClient
from curb_energy import models


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

is_streaming = False


def stop():
    global is_streaming
    is_streaming = False


async def stream(client: RealTimeClient):
    global is_streaming
    is_streaming = True

    while is_streaming:
        if not client.is_connected:
            await client.connect()

        data = await client.read()
        logger.info(data)

    await client.disconnect()


async def main(args: argparse.Namespace, event_loop: asyncio.AbstractEventLoop):
    l = event_loop if event_loop is not None else asyncio.get_event_loop()
    clients = []

    async with RestApiClient(username=args.username, password=args.password,
                             loop=l) as client:
        for profile in await client.profiles():
            r_client = RealTimeClient(config=profile.real_time[0])
            await r_client.connect()
            clients.append(r_client)

    await asyncio.gather(*[stream(c) for c in clients], loop=l)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--username',
                        help='Curb API username (env: CURB_USERNAME)',
                        default=os.environ.get('CURB_USERNAME'))

    parser.add_argument('--password',
                        help='Curb API password (env: CURB_PASSWORD)',
                        default=os.environ.get('CURB_PASSWORD'))

    parser.add_argument('--client_id',
                        help='Curb Client ID (env: CURB_CLIENT_ID)',
                        default=os.environ.get('CURB_CLIENT_ID'))

    parser.add_argument('--client_token',
                        help='Curb Client Token (env: CURB_CLIENT_TOKEN)',
                        default=os.environ.get('CURB_CLIENT_TOKEN'))
    return parser


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, stop)
    loop.add_signal_handler(signal.SIGTERM, stop)
    loop.run_until_complete(main(get_parser().parse_args(), loop))
