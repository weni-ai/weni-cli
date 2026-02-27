import jwt
import pytest

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from weni_cli.jwt_generator import generate_jwt_token, DEFAULT_EXPIRATION_MINUTES


@pytest.fixture
def rsa_key_pair():
    """Generate an RSA key pair for testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def test_generate_jwt_token_valid(rsa_key_pair):
    """Test generating a valid JWT token with default expiration."""
    private_pem, public_pem = rsa_key_pair
    project_uuid = "test-project-uuid-1234"

    token = generate_jwt_token(project_uuid, private_pem)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify the token
    decoded = jwt.decode(token, public_pem, algorithms=["RS256"])
    assert decoded["project_uuid"] == project_uuid
    assert "exp" in decoded
    assert "iat" in decoded


def test_generate_jwt_token_custom_expiration(rsa_key_pair):
    """Test generating a JWT token with custom expiration."""
    private_pem, public_pem = rsa_key_pair
    project_uuid = "test-project-uuid-5678"

    token = generate_jwt_token(project_uuid, private_pem, expiration_minutes=120)

    decoded = jwt.decode(token, public_pem, algorithms=["RS256"])
    assert decoded["project_uuid"] == project_uuid
    # Verify that exp - iat is approximately 120 minutes (7200 seconds)
    assert abs((decoded["exp"] - decoded["iat"]) - 7200) < 5


def test_generate_jwt_token_default_expiration(rsa_key_pair):
    """Test that default expiration is applied when not specified."""
    private_pem, public_pem = rsa_key_pair
    project_uuid = "test-project-uuid"

    token = generate_jwt_token(project_uuid, private_pem)

    decoded = jwt.decode(token, public_pem, algorithms=["RS256"])
    expected_seconds = DEFAULT_EXPIRATION_MINUTES * 60
    assert abs((decoded["exp"] - decoded["iat"]) - expected_seconds) < 5


def test_generate_jwt_token_invalid_key():
    """Test that an invalid key raises an exception."""
    with pytest.raises(Exception):
        generate_jwt_token("project-uuid", "not-a-valid-key")


def test_generate_jwt_token_algorithm_is_rs256(rsa_key_pair):
    """Test that the token uses RS256 algorithm."""
    private_pem, public_pem = rsa_key_pair

    token = generate_jwt_token("project-uuid", private_pem)

    # Get the header without verification
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "RS256"
