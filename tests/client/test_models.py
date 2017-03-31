from curb_energy.client import AuthToken
from curb_energy import models


def test_token_equality():
    t1 = AuthToken()
    t2 = AuthToken()

    assert t1 == t2

    t1 = AuthToken(user_id=100,
                   access_token='abc',
                   refresh_token='def',
                   expires_in=300)

    t2.user_id = 100
    t2.access_token = 'abc'
    t2.refresh_token = 'def'
    t2.expires_in = 300

    assert t1 == t2

    # Tokens may have been generated at different times, but that dpesn't
    # affect equality checks
    assert t1.generated_on != t2.generated_on

    # Expiration period is ignored
    t2.expires_in -= 5
    assert t1 == t2 and t1.expires_in != t2.expires_in
    assert t1.expiry != t2.expiry


def test_token_inequality():
    t1 = AuthToken(access_token='abc', refresh_token='def', user_id=100)
    assert t1 != {} and not (t1 == {})

    t2 = AuthToken(access_token='abc', refresh_token='def', user_id=200)
    assert t1 != t2


def test_sensor():
    s1 = models.Sensor(id=1, name='name', arbitrary_name='other')
    s2 = models.Sensor()
    s2.id = 1
    s2.name = 'name'
    s2.arbitrary_name = 'other'

    assert s1 == s2

    s2.name = s2.arbitrary_name
    assert s1 != s2

    assert s1 != {} and not s1 == {}


def test_sensor_group():
    s = models.Sensor()
    sg1 = models.SensorGroup(id=1, sensors=[s])

    sg2 = models.SensorGroup()
    sg2.id = 1
    sg2.sensors = [s]

    assert sg1 == sg2
    sg2.sensors = [s, None]

    assert sg1 != sg2

    assert sg1 != {} and not sg1 == {}


def test_register():
    r1 = models.Register(id=1, label='x', multiplier=1, flip_domain=False)
    r2 = models.Register()
    r2.id = 1
    r2.label = 'x'
    r2.multiplier = 1
    r2.flip_domain = False

    assert r1 == r2

    r2.flip_domain = True
    assert r1 != r2

    assert r1 != {} and not r1 == {}


def test_profile():
    p1 = models.Profile(id=1)
    p2 = models.Profile(display_name='hello')
    p2.id = 1

    # Equality is based on ID only (for now)
    assert p1 == p2

    p2.id = 2
    assert p1 != p2

    assert p1 != {} and not p1 == {}


def test_find_register_by_id():
    registers = [models.Register(id=i) for i in range(0, 5)]
    profile = models.Profile(id=1, registers=registers)

    assert profile.find_register(0) == registers[0]
    assert profile.find_register(88) is None


def test_device():
    d1 = models.Device(id=1)
    d2 = models.Device()
    d2.id = 1

    assert d1 == d2

    d1.id = 0
    assert d1 != d2

    assert d1 != {} and not d1 == {}


def test_billing_model():
    m1 = models.BillingModel(name='hello')
    m2 = models.BillingModel()
    m2.name = 'hello'

    assert m1 == m2

    m1.name = 'hi'
    assert m1 != m2

    assert m1 != {} and not m1 == {}


def test_billing():
    m1 = models.Billing(profile_id=1)
    m2 = models.Billing()
    m2.profile_id = 1

    assert m1 == m2

    m1.profile_id = 0
    assert m1 != m2

    assert m1 != {} and not m1 == {}
