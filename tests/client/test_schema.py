import pytest
import os
from curb_energy import schema


def load(*args):
    with open(os.path.join(*args)) as f:
        return f.read()


@pytest.mark.parametrize(
    ['filename', 'schema'],
    [
        ('device.json', schema.DeviceSchema),
        ('devices.json', schema.DevicesSchema),
        ('entrypoint.json', schema.EntryPointSchema),
        ('profile.json', schema.ProfileSchema),
        ('profile_billing.json', schema.BillingSchema),
        ('profile_registers.json', schema.RegistersSchema),
        ('profiles.json', schema.ProfilesSchema),
        ('sensor.json', schema.SensorSchema),
        ('sensor_group.json', schema.SensorGroupSchema),
    ]
)
def test_transformation(rest_fixtures_dir, schema, filename):
    buf = load(rest_fixtures_dir, filename)

    schema_instance = schema()

    # Make sure that loading is without errors
    model, err = schema_instance.loads(buf)
    assert model
    assert not err

    # Make sure that serializing is without errors
    serialized, err = schema_instance.dumps(model)
    assert serialized
    assert not err

    # deserialize -> serialize -> deserialize equality

    loaded, err = schema_instance.loads(serialized)
    assert model == loaded
    assert not err


def test_historical(rest_fixtures_dir):
    buf = load(rest_fixtures_dir, 'profile_historical_data.json')
    h = schema.HistoricalData().loads(buf)
    assert h
