from typing import Any

import jwt
import jwt.exceptions

from ai.backend.common.types import BackendAISchema
from ai.backend.common.utils import nmget

from .exception import ExpiredSToken, InvalidSToken

KEYPAIR_PLUGIN_CONFIG_KEY = "plugins.webapp.keypair_auth"


class STokenData(BackendAISchema):
    access_key: str
    secret_key: str


def get_plugin_config(shared_config: dict[str, Any]) -> Any:
    return nmget(shared_config, KEYPAIR_PLUGIN_CONFIG_KEY)


def encode_jwt_token(token_data: dict[str, Any], secret: str) -> str:
    return jwt.encode(token_data, secret, algorithm="HS256")


def decode_jwt_token(val: str, secret: str) -> dict[str, Any]:
    result: dict[str, Any] = jwt.decode(val, secret, algorithms=["HS256"])
    return result


def serialize_stoken(data: STokenData, secret: str) -> str:
    return encode_jwt_token(data.model_dump(mode="json"), secret=secret)


def deserialize_stoken(val: str, secret: str) -> STokenData:
    try:
        raw = decode_jwt_token(val, secret=secret)
        return STokenData.model_validate(raw)
    except jwt.ExpiredSignatureError:
        raise ExpiredSToken from None
    except (jwt.PyJWTError, KeyError):
        raise InvalidSToken from None
