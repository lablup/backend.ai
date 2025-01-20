import enum
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import bcrypt
import humps
from pydantic import BaseModel

from ai.backend.common.types import HostPortPair


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt(rounds=12)).decode("utf8")


def verify_password(guess: str, hashed: str) -> bool:
    return bcrypt.checkpw(guess.encode("utf8"), hashed.encode("utf8"))


def ensure_json_serializable(o: Any) -> Any:
    match o:
        case dict():
            return {ensure_json_serializable(k): ensure_json_serializable(v) for k, v in o.items()}
        case list():
            return [ensure_json_serializable(x) for x in o]
        case UUID():
            return str(o)
        case HostPortPair():
            return {"host": o.host, "port": o.port}
        case Path():
            return o.as_posix()
        case BaseModel():
            return ensure_json_serializable(o.model_dump())
        case enum.Enum():
            return o.value
        case datetime():
            return o.timestamp()
        case _:
            return o


# TODO: Use pydantic alias_generators after v2.8
# ref: https://docs.pydantic.dev/2.8/api/config/#pydantic.alias_generators.to_snake
def config_key_to_snake_case(o: Any) -> Any:
    match o:
        case dict():
            return {humps.dekebabize(k): config_key_to_snake_case(v) for k, v in o.items()}
        case list():
            return [config_key_to_snake_case(i) for i in o]
        case _:
            return o


def config_key_to_kebab_case(o: Any) -> Any:
    match o:
        case dict():
            return {humps.kebabize(k): config_key_to_kebab_case(v) for k, v in o.items()}
        case list():
            return [config_key_to_kebab_case(i) for i in o]
        case _:
            return o
