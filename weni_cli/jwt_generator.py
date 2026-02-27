import jwt

from datetime import datetime, timedelta, timezone
from typing import Optional


DEFAULT_EXPIRATION_MINUTES = 60


def generate_jwt_token(
    project_uuid: str,
    secret_key: str,
    expiration_minutes: Optional[int] = None,
) -> str:
    """
    Generate JWT token for project UUID.

    Args:
        project_uuid: The project UUID to include in the token payload.
        secret_key: The RSA private key (PEM format) used to sign the token.
        expiration_minutes: Optional token expiration time in minutes.
                           If not provided, uses default (60 minutes).

    Returns:
        The encoded JWT token string.
    """
    exp_minutes = expiration_minutes or DEFAULT_EXPIRATION_MINUTES
    payload = {
        "project_uuid": project_uuid,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=exp_minutes),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret_key, algorithm="RS256")
