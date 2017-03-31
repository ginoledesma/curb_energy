import pytest
import os
import vcr


here = os.path.dirname(__file__)


@pytest.fixture
def fixtures_dir():
    return os.path.join(here, '..', 'fixtures')


@pytest.fixture
def cassettes_fixtures_dir(fixtures_dir):
    return os.path.join(fixtures_dir, 'cassettes')


@pytest.fixture
def rest_fixtures_dir(fixtures_dir):
    return os.path.join(fixtures_dir, 'rest_responses')


vcr.default_vcr = vcr.VCR(
    cassette_library_dir=cassettes_fixtures_dir(fixtures_dir()),
    record_mode='none',
)
vcr.use_cassette = vcr.default_vcr.use_cassette
