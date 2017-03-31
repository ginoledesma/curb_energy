"""
Classes for representing the Curb API resources
"""


from collections import namedtuple
from typing import List
from typing import Optional


class BaseModel(object):
    pass


class RealTimeConfig(BaseModel):
    """
    Configuration for the Real-Time client
    """
    def __init__(self,
                 topic: str=None,
                 format: str='curb',
                 prefix: str=None,
                 ws_url: str=None,
                 **kwargs):
        """
        Create an instance of the RealTime configuration object        

        :param topic: The MQTT topic to subscribe to  
        :param format: Output format (currently only accepts 'curb') 
        :param prefix: A prefix for each key within the measurement results
        :param ws_url: The URL to the real-time API 
        """
        self.topic = topic
        self.format = format
        self.prefix = prefix
        self.ws_url = ws_url

    @property
    def url(self) -> str:
        return self.ws_url

    def __repr__(self):  # pragma: no cover
        return '%s:%s:%s:%s' % (self.topic, self.format, self.prefix,
                                self.ws_url)


class BillingModel(BaseModel):
    """
    The Billing Model describes the utility and billing tier for a given 
    customer.     
    """
    RESIDENTIAL = 'Residential'
    COMMERCIAL = 'Commercial'
    SECTORS = [RESIDENTIAL, COMMERCIAL]

    def __init__(self,
                 sector: str=RESIDENTIAL,
                 label: str=None,
                 utility: str=None,
                 name: str=None,
                 **kwargs):
        """
        Create an instance of the billing model for the customer

        :param sector: One of 'Residental' or 'Commercial' 
        :param label: Unique ID of this instance 
        :param utility: The name of the utility / power provider 
        :param name: The billing tier 
        """
        self.name = name
        self.sector = sector
        self.label = label
        self.utility = utility

    @property
    def is_commercial(self):  # pragma: no cover
        return self.sector == self.COMMERCIAL

    @property
    def is_residential(self): # pragma: no cover
        return self.sector == self.RESIDENTIAL

    def __eq__(self, other):
        if not isinstance(other, BillingModel):
            return NotImplemented

        attrs = ['name', 'sector', 'label', 'utility']
        return all([getattr(self, a) == getattr(other, a) for a in attrs])

    def __ne__(self, other):
        if not isinstance(other, BillingModel):
            return NotImplemented

        attrs = ['name', 'sector', 'label', 'utility']
        return any([getattr(self, a) != getattr(other, a) for a in attrs])


class Billing(BaseModel):
    """
    Billing describes how and when the customer is billed and is associated 
    with a :class:`BillingModel` instance.     
    """
    def __init__(self,
                 profile_id: int=-1,
                 billing_model: BillingModel=None,
                 day_of_month: int=1,
                 zip_code: int=None,
                 dollar_per_kwh: float=None,
                 **kwargs):
        """
        The billing configuration for the customer

        :param profile_id: The Curb configuration profile 
        :param billing_model: Billing model information 
        :param day_of_month: The start day of the billing period 
        :param zip_code: The zip code of the dwelling being monitored  
        :param dollar_per_kwh: The price per kilowatt-hour 
        """
        self.profile_id = profile_id
        self.billing_model = billing_model
        self.day_of_month = day_of_month
        self.zip_code = zip_code
        self.dollar_per_kwh = dollar_per_kwh

    @property
    def url(self) -> str:  # pragma: no cover
        return '/api/profiles/%d/billing' % self.profile_id

    def __eq__(self, other):
        if not isinstance(other, Billing):
            return NotImplemented

        attrs = ['profile_id', 'billing_model', 'day_of_month', 'zip_code',
                 'dollar_per_kwh']
        return all([getattr(self, a) == getattr(other, a) for a in attrs])

    def __ne__(self, other):
        if not isinstance(other, Billing):
            return NotImplemented

        attrs = ['profile_id', 'billing_model', 'day_of_month', 'zip_code',
                 'dollar_per_kwh']
        return any([getattr(self, a) != getattr(other, a) for a in attrs])


class Sensor(BaseModel):
    """
    An energy monitoring device (in this case, the Curb Hub) 
    """
    def __init__(self,
                 id: int=-1,
                 name: str=None,
                 arbitrary_name: str=None,
                 **kwargs):
        """
        Creates an instance of a Sensor

        :param id: Unique identifier
        :param name: Unique name (serial number) of the Curb Hub
        :param arbitrary_name: User-assigned name for the Curb Hub
        """
        self.id = id
        self.name = name
        self.arbitrary_name = arbitrary_name

    @property
    def url(self) -> str:  # pragma: no cover
        return '/api/sensors/%d' % self.id

    def __eq__(self, other):
        if not isinstance(other, Sensor):
            return NotImplemented

        attrs = ['id', 'name', 'arbitrary_name']
        return all([getattr(self, a) == getattr(other, a) for a in attrs])

    def __ne__(self, other: 'Sensor'):
        if not isinstance(other, Sensor):
            return NotImplemented

        attrs = ['id', 'name', 'arbitrary_name']
        return any([getattr(self, a) != getattr(other, a) for a in attrs])

    def __repr__(self):  # pragma: no cover
        return 'Sensor-%s (%s)' % (self.id, self.name)


class SensorGroup(BaseModel):
    """
    A logical grouping of sensors
    """
    def __init__(self,
                 id: int=-1,
                 sensors: Optional[List[Sensor]]=None,
                 **kwargs):
        """
        Creates a logical grouping of sensors identified by a unique ID

        :param id: The unique ID of the sensor group
        :param sensors: List of sensors associated with this group
        """
        self.id = id
        self.sensors = sensors if sensors is not None else []

    @property
    def url(self) -> str:  # pragma: no cover
        return '/api/sensor_groups/%d' % self.id

    def __eq__(self, other: 'SensorGroup'):
        if not isinstance(other, SensorGroup):
            return NotImplemented

        return self.id == other.id and self.sensors == other.sensors

    def __ne__(self, other: 'SensorGroup'):
        if not isinstance(other, SensorGroup):
            return NotImplemented

        return self.id != other.id or self.sensors != other.sensors

    def __repr__(self):  # pragma: no cover
        return 'SensorGroup-%s (%s)' % (self.id, self.sensors)


class Device(BaseModel):
    """
    A logical grouping of Sensor Groups. A "device" can be thought of as a 
    unit representing a location being measured, such as a home.
    
    .. todo::
    
        Clarify with Curb what they really intend by this.
    """

    def __init__(self,
                 id: int=-1,
                 building_type: str=None,
                 name: str=None,
                 timezone: str=None,
                 sensor_groups: List[SensorGroup]=None,
                 **kwargs):
        """
        Creates an instance of a dwelling location
        
        :param id: The unique ID of this monitored unit 
        :param building_type: The type of building (home, commercial) 
        :param name: The name of the monitored unit  
        :param timezone: Timezone label
        :param sensor_groups: List of sensor groups associated 
        """
        self.id = id
        self.building_type = building_type
        self.name = name
        self.timezone = timezone
        self.sensor_groups = sensor_groups if sensor_groups is not None else []

    @property
    def url(self) -> str:  # pragma: no cover
        return '/api/devices/%d' % self.id

    def __eq__(self, other):
        if not isinstance(other, Device):
            return NotImplemented

        attrs = ['id', 'name', 'building_type', 'timezone', 'sensor_groups']
        return all([getattr(self, a) == getattr(other, a) for a in attrs])

    def __ne__(self, other):
        if not isinstance(other, Device):
            return NotImplemented

        attrs = ['id', 'name', 'building_type', 'timezone', 'sensor_groups']
        return any([getattr(self, a) != getattr(other, a) for a in attrs])

    def __repr__(self):  # pragma: no cover
        return 'Device-%s (%s)' % (self.id, self.name)


class Register(BaseModel):
    """
    A source of power measurement data.
    """

    def __init__(self,
                 id: str='',
                 multiplier: int=1,
                 flip_domain: bool=False,
                 label: str=None,
                 **kwargs):
        """
        Creates an instance of a source of power measurement data, such as an
        individual circuit breaker of electic panel 
        
        :param id: Unique identifier
        :param multiplier: Power multiplier
        :param flip_domain: Invert the sign of the reported values (pos/neg)
        :param label: Name of the power source
        """
        self.id = id
        self.label = label
        self.multiplier = multiplier
        self.flip_domain = flip_domain

    def __repr__(self):  # pragma: no cover
        return 'Register-%s (%s)' % (self.id, self.label)

    def __eq__(self, other):
        if not isinstance(other, Register):
            return NotImplemented

        attrs = ['id', 'label', 'flip_domain', 'multiplier']
        return all([getattr(self, a) == getattr(other, a) for a in attrs])

    def __ne__(self, other):
        if not isinstance(other, Register):
            return NotImplemented

        attrs = ['id', 'label', 'flip_domain', 'multiplier']
        return any([getattr(self, a) != getattr(other, a) for a in attrs])


class RegisterGroup(BaseModel):
    """
    A logical grouping of registers according to classification
    """
    def __init__(self,
                 grid: Optional[List[Register]],
                 normals: Optional[List[Register]],
                 solar: Optional[List[Register]],
                 use: Optional[List[Register]],
                 ):
        """
        A group of registers
        
        :param grid: Circuit breakers from the grid
        :param normals: "Normal" (non-grid) circuit breakers
        :param solar: Circuit breakers from solar power
        :param use: Used power
        """
        self.grid = grid if grid is not None else []
        self.normals = normals if normals is not None else []
        self.solar = solar if solar is not None else []
        self.use = use if use is not None else []

    def __repr__(self):  # pragma: no cover
        return 'grid=%d:normals=%d:solar=%d:use=%d' % (len(self.grid),
                                                       len(self.normals),
                                                       len(self.solar),
                                                       len(self.use))


class Profile(BaseModel):
    """
    A profile defines how to interpret data, access real time data, 
    and various other configuration options.
    """
    def __init__(self,
                 id: int=-1,
                 display_name: str=None,
                 real_time: RealTimeConfig=None,
                 register_groups: List[RegisterGroup]=None,
                 registers: List[Register]=None,
                 widgets: List[type]=None,
                 billing: Billing=None,
                 **kwargs):
        """
        Create an instance of a configuration profile
        
        :param id: The unique ID of the profile 
        :param display_name: The friendly name of this profile/configuration 
        :param real_time: The configuration for the real-time API 
        :param register_groups: The register groups associated with this config 
        :param registers: The list of registers associated with this config 
        :param widgets: The list of widgets
        :param billing: The billing configuration 
        """
        self.id = id
        self.billing = billing
        self.display_name = display_name
        self.register_groups = register_groups
        self.registers = registers if registers is not None else []
        self.real_time = real_time
        self.widgets = widgets

    @property
    def url(self) -> str:   # pragma: no cover
        return '/api/profiles/%d' % self.id

    def find_register(self, id: str) -> Optional[Register]:
        """
        Return a Register by its unique ID, or :class:`None` if not found
        
        :param id: The unique ID of the register to look up
        """
        return next((r for r in self.registers if r.id == id), None)

    def __repr__(self):   # pragma: no cover
        return "Profile-%s" % self.id

    def __eq__(self, other):
        if not isinstance(other, Profile):
            return NotImplemented

        # FIXME: for now, we only match based on ID
        return self.id == other.id

    def __ne__(self, other):
        if not isinstance(other, Profile):
            return NotImplemented

        return self.id != other.id


Measurement = namedtuple('Measurement', ['granularity',
                                         'since',
                                         'until',
                                         'unit',
                                         'headers',
                                         'data'])
