import pytest
from curb_energy.client import AuthToken


@pytest.fixture
def token():
    return AuthToken(access_token='12345',
                     refresh_token='12345',
                     expires_in=300,
                     user_id=101,
                     )


def test_blank_tokens_are_invalid():
    t = AuthToken()
    assert not t.is_valid


def test_expired_tokens(token):
    assert token.is_valid

    # Forcibly set the expiration counter to 5 minutes ago
    token.expires_in = -300
    assert not token.is_valid


def test_transformation(token):
    assert token == AuthToken.from_json(token.json())
