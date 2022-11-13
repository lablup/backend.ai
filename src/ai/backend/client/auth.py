import enum
import hashlib
import hmac
from datetime import datetime
from typing import Mapping, Tuple

import attrs
from yarl import URL

__all__ = (
    "AuthToken",
    "AuthTokenTypes",
    "generate_signature",
)


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
