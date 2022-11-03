"""
Wrapper of msgpack-python with good defaults.
"""

import datetime
import enum
import pickle
import uuid
from decimal import Decimal
from typing import Any

import msgpack as _msgpack
import temporenc

__all__ = ("packb", "unpackb")


class ExtTypes(enum.IntEnum):
    # We can define up to 255 extension type identifiers.
    UUID = 1
    DATETIME = 16
    DECIMAL = 32
    BINARY_SIZE = 33


def _default(obj: object) -> _msgpack.ExtType:
    match obj:
        case uuid.UUID():
            return _msgpack.ExtType(ExtTypes.UUID, obj.bytes)
        case datetime.datetime():
            return _msgpack.ExtType(ExtTypes.DATETIME, temporenc.packb(obj))
        case Decimal():
            return _msgpack.ExtType(ExtTypes.DECIMAL, pickle.dumps(obj, protocol=5))
    raise TypeError("Unknown type: %r" % (obj,))


def _ext_hook(code: int, data: bytes) -> Any:
    match code:
        case ExtTypes.UUID:
            return uuid.UUID(bytes=data)
        case ExtTypes.DATETIME:
            return temporenc.unpackb(data).datetime()
        case ExtTypes.DECIMAL:
            return pickle.loads(data)
    return _msgpack.ExtType(code, data)


def packb(data: Any, **kwargs) -> bytes:
    opts = {"use_bin_type": True, **kwargs}
    return _msgpack.packb(data, default=_default, **opts)


def unpackb(packed: bytes, **kwargs) -> Any:
    opts = {"raw": False, "use_list": False, **kwargs}
    return _msgpack.unpackb(packed, ext_hook=_ext_hook, **opts)
