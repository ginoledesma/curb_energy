"""
The schema module helps convert the Curb API REST resources into 
Python-friendly objects.
"""
import logging
from marshmallow import Schema
from marshmallow import fields
from marshmallow import validate
from marshmallow import pre_dump
from marshmallow import pre_load
from marshmallow import post_load
from curb_energy import models


logger = logging.getLogger(__name__)


class HyperLink(Schema):
    href = fields.String(required=True)
    methods = fields.List(fields.String)


class BaseSchema(Schema):
    class Links(Schema):
        self = fields.Nested(HyperLink)

    _links = fields.Nested(Links)


class SensorSchema(BaseSchema):
    """
    An energy measuring device, like the Curb Hub
    """
    id = fields.Integer(required=True)
    name = fields.String()
    arbitrary_name = fields.String()

    @pre_load
    def pre_deserialize(self, data):
        links = data.get('_links', {})

        if 'id' not in data:
            l = links.get('self', {}).get('href', '')
            data['id'] = l.lstrip('/api/sensors/')

        return data

    @post_load
    def create_model(self, data):
        return models.Sensor(**data)


class SensorGroupSchema(BaseSchema):
    """
    A group of one or more Sensors measuring power at a common location
    """
    class Embedded(BaseSchema):
        sensors = fields.Nested(SensorSchema, many=True)

    id = fields.Integer()
    _embedded = fields.Nested(Embedded)

    @pre_load
    def pre_deserialize(self, data):
        links = data.get('_links', {})

        if 'id' not in data:
            l = links.get('self', {}).get('href', '')
            data['id'] = l.lstrip('/api/sensor_groups/')

        return data

    @pre_dump
    def pre_serialize(self, data):
        d = {k: getattr(data, k) for k in vars(data)}
        d['_embedded'] = {'sensors': d.pop('sensors')}
        return d

    @post_load
    def create_model(self, data):
        embedded = data.pop('_embedded', {})
        data['sensors'] = embedded.get('sensors', [])
        return models.SensorGroup(**data)


class DeviceSchema(BaseSchema):
    """
    A monitored "location", such as a home/building.

    .. todo::
    
        Why does Curb API call it "Device"?
    """
    class Embedded(BaseSchema):
        sensor_groups = fields.Nested(SensorGroupSchema, many=True)

    id = fields.Integer(required=True)
    name = fields.String()
    building_type = fields.String()
    timezone = fields.String()
    _embedded = fields.Nested(Embedded)

    @pre_load
    def pre_deserialize(self, data):
        links = data.get('_links', {})

        if 'id' not in data:
            l = links.get('self', {}).get('href', '')
            data['id'] = l.lstrip('/api/devices/')

        return data

    @pre_dump
    def pre_serialize(self, data):
        d = {k: getattr(data, k) for k in vars(data)}
        d['_embedded'] = {'sensor_groups': d.pop('sensor_groups')}
        return d

    @post_load
    def create_model(self, data):
        embedded = data.pop('_embedded', {})
        data['sensor_groups'] = embedded.get('sensor_groups', [])
        return models.Device(**data)


class BillingModelSchema(BaseSchema):
    """
    Billing Model: Utility/Provider information
    """
    sector = fields.String(validate=validate.OneOf(models.BillingModel.SECTORS))
    label = fields.String()
    utility = fields.String()
    name = fields.String()

    @post_load
    def create_model(self, data):
        return models.BillingModel(**data)


class BillingSchema(BaseSchema):
    """
    Billing Information for the monitored location
    """
    id = fields.Integer()
    billing_model = fields.Nested(BillingModelSchema)
    day_of_month = fields.Integer(load_from='billing_day_of_month',
                                  dump_to='billing_day_of_month')
    zip_code = fields.Integer()
    dollar_per_kwh = fields.Float(load_from='dollar_pkwh',
                                  dump_to='dollar_pkwh')

    @post_load
    def create_model(self, data):
        return models.Billing(**data)


class RegisterSchema(BaseSchema):
    """
    Source for a single stream of power data. They can correspond to a
    physical circuit breaker.
    """

    ID_REGEX = r'^urn:energycurb:registers:curb:[a-zA-z0-9]+:[0-9]+:[a-f]$'

    id = fields.String(validate=validate.Regexp(ID_REGEX))
    label = fields.String()
    flip_domain = fields.Boolean(allow_none=False, default=False, missing=False)
    multiplier = fields.Integer()

    @post_load
    def create_model(self, data):
        return models.Register(**data)


class RegistersSchema(BaseSchema):
    """
    A Collection of Registers
    """
    registers = fields.Nested(RegisterSchema, many=True)


class RegisterGroupsSchema(Schema):
    """
    A logical grouping of Registers.
    """
    id = fields.Integer()
    display_name = fields.String()
    use = fields.Nested(RegisterSchema, many=True)
    solar = fields.Nested(RegisterSchema, many=True)
    normals = fields.Nested(RegisterSchema, many=True)
    grid = fields.Nested(RegisterSchema, many=True)

    @post_load
    def create_model(self, data):
        return models.RegisterGroup(**data)


class RealTimeSchema(Schema):
    """
    Source for Real-time data
    """
    class Links(Schema):
        ws = fields.Nested(HyperLink)

    format = fields.String()
    topic = fields.String()
    prefix = fields.String()

    _links = fields.Nested(Links)

    @post_load
    def create_model(self, data):
        ws_url = data.get('_links', {}).get('ws', {}).get('href')
        return models.RealTimeConfig(ws_url=ws_url, **data)


class ProfileSchema(Schema):
    """
    Profiles define how to interpret data, access real time data, and various
    other configuration options.
    """
    class Embedded(Schema):
        billing = fields.Nested(BillingSchema)
        registers = fields.Nested(RegistersSchema)

    id = fields.Integer()
    display_name = fields.String()
    real_time = fields.Nested(RealTimeSchema, many=True)
    register_groups = fields.Nested(RegisterGroupsSchema)

    _embedded = fields.Nested(Embedded)
    billing = fields.Nested(BillingSchema, load_only=True)
    registers = fields.Nested(RegisterSchema, many=True, load_only=True)

    @pre_dump
    def pre_serialize(self, data):
        d = {k: getattr(data, k) for k in vars(data)}
        d['_embedded'] = {
            'billing': d.pop('billing', {}),
            'registers': {'registers': d.pop('registers', [])}
        }
        return d

    @post_load
    def create_model(self, data):
        embedded = data.pop('_embedded', {})
        data['billing'] = embedded.pop('billing')
        # registers is nested
        data['registers'] = embedded.pop('registers').get('registers')
        profile = models.Profile(**data)

        register_map = {r.id: r for r in profile.registers}

        for g in ['use', 'normals', 'grid', 'solar']:
            group = getattr(profile.register_groups, g)
            for register in list(group):
                if register.id in register_map:
                    group.remove(register)
                    group.append(register_map[register.id])

        return profile


class DevicesSchema(BaseSchema):
    devices = fields.Nested(DeviceSchema, many=True)


class ProfilesSchema(BaseSchema):
    class Embedded(BaseSchema):
        profiles = fields.Nested(ProfileSchema, many=True)

    _embedded = fields.Nested(Embedded)

    @pre_dump
    def pre_serialize(self, data):
        d = dict(data)
        d['_embedded'] = {'profiles': d.pop('profiles')}
        return d

    @post_load
    def create_model(self, data):
        embedded = data.pop('_embedded', {})
        data['profiles'] = embedded.get('profiles', [])
        return data


class EntryPointSchema(BaseSchema):
    class Links(Schema):
        devices = fields.Nested(HyperLink)
        profiles = fields.Nested(HyperLink)
        self = fields.Nested(HyperLink)

    _links = fields.Nested(Links)

    @pre_dump
    def pre_serialize(self, data):
        if '_links' not in data:
            return {'_links': data}
        return data

    @post_load
    def create_model(self, data):
        return data['_links']


class HistoricalData(BaseSchema):
    granularity = fields.String(validate=validate.OneOf(['1D', '1H', '1T']))
    since = fields.Integer(default=0, missing=0)
    until = fields.Integer(default=0, missing=0)
    unit = fields.String(validate=validate.OneOf(['w', '$/hr']))
    headers = fields.List(fields.String)
    data = fields.List(fields.List(fields.Float))

    @pre_load
    def pre_deserialize(self, data):
        results = data.get('results', [])
        return results[0] if results else {}

    @post_load
    def create_model(self, data):
        return models.Measurement(granularity=data['granularity'],
                                  since=data['since'],
                                  until=data['until'],
                                  unit=data['unit'],
                                  headers=data['headers'],
                                  data=data['data'])
