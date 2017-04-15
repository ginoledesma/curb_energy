import argparse
import asyncio
import csv
import logging
import os
import sys
import textwrap
from curb_energy.client import AuthToken
from curb_energy.client import RealTimeClient
from curb_energy.client import RestApiClient
from curb_energy import models


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


def _print(t, indent=0):
    print(textwrap.indent(textwrap.dedent(t).strip(), prefix=' ' * indent))


def show_token(token: AuthToken):
    buf = """
    Access Token: {access_token} 
    Refresh Token: {refresh_token}
    Expires in: {expires}
    User ID: {user_id}
    Token Type: {token_type}
    """.format(access_token=token.access_token,
               refresh_token=token.refresh_token,
               expires=token.expiry,
               user_id=token.user_id,
               token_type=token.token_type)
    _print(buf)
    

def show_sensor(sensor: models.Sensor, indent=0):
    buf = """
    Sensor ID: {id}
    Name: {arbitrary_name} ({name})
    """.format(id=sensor.id,
               arbitrary_name=sensor.arbitrary_name,
               name=sensor.name)
    _print(buf, indent=indent)


def show_sensor_group(sensor_group: models.SensorGroup, indent=0):
    buf = """
    Sensor Group ID: {id}
    
    Sensors:
    """.format(id=sensor_group.id)

    _print(buf, indent=indent)
    for s in sensor_group.sensors:
        show_sensor(s, indent=indent+1)


def show_device(device: models.Device, indent=0):
    buf = """
    Device ID: {id}
    Name: {name}
    Building Type: {building_type}
    Timezone: {timezone}
    """.format(id=device.id,
               name=device.name,
               building_type=device.building_type,
               timezone=device.timezone)
    _print(buf, indent=indent)

    _print('Sensor Groups:')
    for sg in device.sensor_groups:
        show_sensor_group(sg, indent=indent+1)
    print('')


def show_billing(billing: models.Billing, indent=0):
    buf = """
    Provider: {utility}
    Zip Code: {zip_code}
    Day of Month: {day_of_month}
    USD per Kilowatt-Hour: {dollar_per_kwh}
    """.format(
        utility=billing.billing_model.utility,
        zip_code=billing.zip_code,
        day_of_month=billing.day_of_month,
        dollar_per_kwh=billing.dollar_per_kwh
    )
    _print(buf, indent=indent)


def show_realtime(config: models.RealTimeConfig, indent=0):
    buf = """Real-Time API:
    URL: {ws_url}
    Topic: {topic}
    Prefix: {prefix}
    Format: {fmt}
    """.format(ws_url=config.url,
               topic=config.topic,
               prefix=config.prefix,
               fmt=config.format)
    _print(buf, indent=indent)


def show_profile(profile: models.Profile, indent=0):
    buf = """
    Profile ID: {id}
    
    Billing:
    """.format(id=profile.id)

    _print(buf, indent=indent)
    show_billing(profile.billing, indent=indent+1)
    print('')
    show_realtime(profile.real_time[0], indent=indent+1)
    print('')


def show_measurement(data: models.Measurement):
    prefix = 'urn:energycurb:registers:curb:'
    offset = len(prefix)

    writer = csv.writer(sys.stdout)
    headers = [h[offset:] if h.startswith(prefix) else h for h in data.headers]
    writer.writerow(headers)
    for i in data.data:
        writer.writerow(i)


async def main(args: argparse.Namespace, event_loop: asyncio.AbstractEventLoop):
    clients = []
    l = event_loop if event_loop is not None else asyncio.get_event_loop()

    async with RestApiClient(username=args.username,
                             password=args.password,
                             client_secret=args.client_secret,
                             client_token=args.client_token,
                             loop=l) as client:

        if args.fetch_token:
            show_token(await client.fetch_access_token())

        if args.refresh_token:
            show_token(await client.refresh_access_token())

        if args.profiles:
            for profile in await client.profiles():
                show_profile(profile)
                c = RealTimeClient(config=profile.real_time[0])
                clients.append(c)

        if args.devices:
            for device in await client.devices():
                show_device(device)

        if args.historical_data:
            for profile in await client.profiles():
                x = await client.historical_data(profile_id=profile.id,
                                                 granularity=args.granularity,
                                                 unit=args.unit,
                                                 since=args.since,
                                                 until=args.until,)
                show_measurement(x)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument('--username', help='Curb API username',
                        default=os.environ.get('CURB_USERNAME'))

    parser.add_argument('--password', help='Curb API password',
                        default=os.environ.get('CURB_PASSWORD'))

    parser.add_argument('--client_token', help='Curb Client Token',
                        default=os.environ.get('CURB_CLIENT_TOKEN'))

    parser.add_argument('--client_secret', help='Curb Client Secret',
                        default=os.environ.get('CURB_CLIENT_SECRET'))

    parser.add_argument('--profiles', action='store_const', const=True,
                        help='Show the profile configuration')

    parser.add_argument('--devices', action='store_const', const=True,
                        help='Show the list of devices')

    # Access Tokens
    parser.add_argument('--fetch-token', action='store_const', const=True,
                        help='Get and display the access token')

    parser.add_argument('--refresh-token', action='store_const', const=True,
                        help='Refresh the access token')

    # Historical Data reporting
    parser.add_argument('--historical-data', action='store_const', const=True,
                        help='Display the historical data for the user')

    parser.add_argument('--granularity',
                        choices=[RestApiClient.PER_MIN,
                                 RestApiClient.PER_HOUR,
                                 RestApiClient.PER_DAY,
                                 ],
                        default=RestApiClient.PER_HOUR,
                        help='Historical Data granularity')

    parser.add_argument('--since', type=int, default=0,
                        help='Historical data start date (in epoch)')
    parser.add_argument('--until', type=int, default=None,
                        help='Historical data end date (in epoch)')

    parser.add_argument('--unit',
                        choices=[RestApiClient.WATT,
                                 RestApiClient.DOLLAR_PER_HOUR],
                        default=RestApiClient.WATT,
                        help='Historical data reporting unit')
    return parser


if __name__ == '__main__':
    import vcr
    with vcr.VCR(serializer='yaml').use_cassette('/tmp/x.yaml'):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(get_parser().parse_args(), loop))
