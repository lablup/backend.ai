import base64
import secrets
from dataclasses import dataclass

from ai.backend.common.types import AccessKey, SecretKey


@dataclass(frozen=True)
class APIKeypair:
    access_key: AccessKey
    secret_key: SecretKey


def generate_keypair() -> APIKeypair:
    """
    AWS-like access key and secret key generation.
    """
    return APIKeypair(
        access_key=AccessKey("AKIA" + base64.b32encode(secrets.token_bytes(10)).decode("ascii")),
        secret_key=SecretKey(secrets.token_urlsafe(30)),
    )
