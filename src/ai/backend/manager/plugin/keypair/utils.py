from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pydantic import BaseModel

from ai.backend.common.utils import nmget

from .exception import ExpiredSToken, InvalidSToken

KEYPAIR_PLUGIN_CONFIG_KEY = "plugins.webapp.keypair_auth"

# sToken lifetime in seconds.
DEFAULT_STOKEN_TTL_SECONDS = 60
# Clock-skew tolerance when validating the `exp` claim.
STOKEN_LEEWAY_SECONDS = 10


class STokenData(BaseModel):
    access_key: str


def get_plugin_config(shared_config: dict[str, Any]) -> dict[str, Any]:
    config: dict[str, Any] = nmget(shared_config, KEYPAIR_PLUGIN_CONFIG_KEY)
    return config


def encode_jwt_token(token_data: dict[str, Any], secret: str) -> str:
    return jwt.encode(token_data, secret, algorithm="HS256")


def decode_jwt_token(val: str, secret: str) -> Mapping[str, Any]:
    result: dict[str, Any] = jwt.decode(
        val, secret, algorithms=["HS256"], leeway=STOKEN_LEEWAY_SECONDS
    )
    return result


def serialize_stoken(
    data: STokenData, secret: str, ttl_seconds: int = DEFAULT_STOKEN_TTL_SECONDS
) -> str:
    payload = data.model_dump(mode="json")
    now = datetime.now(UTC)
    payload["iat"] = now
    payload["exp"] = now + timedelta(seconds=ttl_seconds)
    return encode_jwt_token(payload, secret=secret)


def deserialize_stoken(val: str, secret: str) -> STokenData:
    try:
        raw = decode_jwt_token(val, secret=secret)
        return STokenData.model_validate(raw)
    except jwt.ExpiredSignatureError:
        raise ExpiredSToken from None
    except (jwt.PyJWTError, KeyError):
        raise InvalidSToken from None
