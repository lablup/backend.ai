import base64
import enum
import secrets

import attrs
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from ai.backend.common.auth.utils import generate_signature

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
