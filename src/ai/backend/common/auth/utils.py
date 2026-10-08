import base64
import hashlib
import hmac
import secrets
from collections.abc import Mapping
from datetime import datetime

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from yarl import URL

from ai.backend.common.types import AccessKey, SecretKey


def generate_signature(
    *,
    method: str,
    version: str,
    endpoint: URL,
    date: datetime,
    rel_url: str,
    content_type: str,
    access_key: str,
    secret_key: str,
    hash_type: str,
) -> tuple[Mapping[str, str], str]:
    """
    Generates the API request signature from the given parameters.
    """
    hash_type = hash_type
    hostname = endpoint.raw_authority
    body_hash = hashlib.new(hash_type, b"").hexdigest()

    sign_str = f"{method.upper()}\n{rel_url}\n{date.isoformat()}\nhost:{hostname}\ncontent-type:{content_type.lower()}\nx-backendai-version:{version}\n{body_hash}"
    sign_bytes = sign_str.encode()

    sign_key = hmac.new(secret_key.encode(), date.strftime("%Y%m%d").encode(), hash_type).digest()
    sign_key = hmac.new(sign_key, hostname.encode(), hash_type).digest()

    signature = hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
    headers = {
        "Authorization": f"BackendAI signMethod=HMAC-{hash_type.upper()}, credential={access_key}:{signature}",
    }
    return headers, signature


def generate_keypair() -> tuple[AccessKey, SecretKey]:
    """
    AWS-like access key and secret key generation.
    """
    ak = "AKIA" + base64.b32encode(secrets.token_bytes(10)).decode("ascii")
    sk = secrets.token_urlsafe(30)
    return AccessKey(ak), SecretKey(sk)


def generate_ssh_keypair() -> tuple[str, str]:
    """
    Generate RSA keypair for SSH/SFTP connection.
    """
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048,
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    ).decode("utf-8")
    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH,
        )
        .decode("utf-8")
    )
    public_key = f"{public_key.rstrip()}\n"
    private_key = f"{private_key.rstrip()}\n"
    return (public_key, private_key)
