import hashlib
import hmac
from collections.abc import Mapping
from datetime import datetime

from yarl import URL


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
