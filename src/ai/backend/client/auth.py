import base64
import enum
import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Mapping, Tuple

import attrs
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from yarl import URL

__all__ = (
    "AuthToken",
    "AuthTokenTypes",
    "generate_signature",
)


_iv_dict = [
    bytes([char]) for char in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
]


class AuthTokenTypes(enum.Enum):
    KEYPAIR = "keypair"
    JWT = "jwt"


@attrs.define()
class AuthToken:
    type = attrs.field(default=AuthTokenTypes.KEYPAIR)  # type: AuthTokenTypes
    content = attrs.field(default=None)  # type: str


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
) -> Tuple[Mapping[str, str], str]:
    """
    Generates the API request signature from the given parameters.
    """
    hash_type = hash_type
    hostname = endpoint._val.netloc  # type: ignore
    body_hash = hashlib.new(hash_type, b"").hexdigest()

    sign_str = "{}\n{}\n{}\nhost:{}\ncontent-type:{}\nx-backendai-version:{}\n{}".format(  # noqa
        method.upper(),
        rel_url,
        date.isoformat(),
        hostname,
        content_type.lower(),
        version,
        body_hash,
    )
    sign_bytes = sign_str.encode()

    sign_key = hmac.new(secret_key.encode(), date.strftime("%Y%m%d").encode(), hash_type).digest()
    sign_key = hmac.new(sign_key, hostname.encode(), hash_type).digest()

    signature = hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
    headers = {
        "Authorization": "BackendAI signMethod=HMAC-{}, credential={}:{}".format(
            hash_type.upper(),
            access_key,
            signature,
        ),
    }
    return headers, signature


def encrypt_payload(endpoint: str, body: bytes) -> bytes:
    iv = b"".join(secrets.choice(_iv_dict) for _ in range(16))
    encoded_endpoint = base64.b64encode(endpoint.encode("utf-8"))
    key = (encoded_endpoint + iv + iv)[:32]
    crypt = AES.new(key, AES.MODE_CBC, iv)
    result = base64.b64encode(crypt.encrypt(pad(body, 16)))
    return iv + b":" + result


def decrypt_payload(endpoint: str, payload: bytes) -> bytes:
    iv, real_payload = payload.split(b":")
    key = (base64.b64encode(endpoint.encode("ascii")) + iv + iv)[:32]
    crypt = AES.new(key, AES.MODE_CBC, iv)
    b64p = base64.b64decode(real_payload)
    return unpad(crypt.decrypt(bytes(b64p)), 16)
