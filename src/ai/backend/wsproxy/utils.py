import base64
import enum
import hashlib
import hmac
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import humps
from pydantic import BaseModel

from ai.backend.common.types import HostPortPair


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


def config_key_to_kebab_case(o: Any) -> Any:
    match o:
        case dict():
            return {humps.kebabize(k): config_key_to_kebab_case(v) for k, v in o.items()}
        case list():
            return [config_key_to_kebab_case(i) for i in o]
        case _:
            return o


def mime_match(base_array: str, compare: str, strict=False) -> bool:
    """
    Checks if `base_array` MIME string contains `compare` MIME type.

    :param: base_array: Array of MIME strings to be compared, concatenated with comma (,) delimiter.
    :param: compare: MIME string to compare.
    :param: strict: If set to True, do not allow wildcard on source MIME type.
    """
    for base in base_array.split(","):
        _base, _, _ = base.partition(";")
        base_left, _, base_right = _base.partition("/")
        compare_left, compare_right = compare.split(";")[0].split("/")
        if (
            not strict
            and (
                (base_left == "*" and base_right == "*")
                or (base_left == compare_left and base_right == "*")
            )
        ) or (base_left == compare_left and base_right == compare_right):
            return True
    return False


def calculate_permit_hash(hash_key: str, user_id: UUID) -> str:
    hash = hmac.new(hash_key.encode(), str(user_id).encode("utf-8"), getattr(hashlib, "sha256"))
    return base64.b64encode(hash.hexdigest().encode()).decode()


def is_permit_valid(hash_key: str, user_id: UUID, hash: str) -> bool:
    valid_hash = calculate_permit_hash(hash_key, user_id)
    return valid_hash == hash
