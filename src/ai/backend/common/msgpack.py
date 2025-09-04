"""
Wrapper of msgpack-python with good defaults.
"""

import datetime
import enum
import os
import pickle
import uuid
from collections.abc import Mapping
from decimal import Decimal
from pathlib import PosixPath, PurePosixPath
from typing import Any, Callable, Optional, Protocol

import msgpack as _msgpack
import temporenc

from .typed_validators import AutoDirectoryPath
from .types import BinarySize, ResourceSlot

__all__ = ("packb", "unpackb")


class ExtTypes(enum.IntEnum):
    # We can define up to 128 extension type identifiers.
    UUID = 1
    DATETIME = 2
    DECIMAL = 3
    POSIX_PATH = 4
    PURE_POSIX_PATH = 5
    ENUM = 6
    IMAGE_REF = 7
    RESOURCE_SLOT = 8
    BACKENDAI_BINARY_SIZE = 16
    AUTO_DIRECTORY_PATH = 17


def _default(obj: object) -> _msgpack.ExtType:
    from .docker import ImageRef

    match obj:
        case tuple():
            return list(obj)
        case uuid.UUID():
            return _msgpack.ExtType(ExtTypes.UUID, obj.bytes)
        case datetime.datetime():
            return _msgpack.ExtType(ExtTypes.DATETIME, temporenc.packb(obj))
        case BinarySize():
            return _msgpack.ExtType(ExtTypes.BACKENDAI_BINARY_SIZE, pickle.dumps(obj, protocol=5))
        case Decimal():
            return _msgpack.ExtType(ExtTypes.DECIMAL, pickle.dumps(obj, protocol=5))
        case PosixPath():
            return _msgpack.ExtType(ExtTypes.POSIX_PATH, os.fsencode(obj))
        case PurePosixPath():
            return _msgpack.ExtType(ExtTypes.PURE_POSIX_PATH, os.fsencode(obj))
        case AutoDirectoryPath():
            return _msgpack.ExtType(ExtTypes.AUTO_DIRECTORY_PATH, os.fsencode(obj))
        case ResourceSlot():
            return _msgpack.ExtType(ExtTypes.RESOURCE_SLOT, pickle.dumps(obj, protocol=5))
        case enum.Enum():
            return _msgpack.ExtType(ExtTypes.ENUM, pickle.dumps(obj, protocol=5))
        case ImageRef():
            return _msgpack.ExtType(ExtTypes.IMAGE_REF, pickle.dumps(obj, protocol=5))
    raise TypeError(f"Unknown type: {obj!r} ({type(obj)})")


class ExtFunc(Protocol):
    def __call__(self, data: bytes) -> Any:
        pass


_DEFAULT_EXT_HOOK: Mapping[ExtTypes, ExtFunc] = {
    ExtTypes.UUID: lambda data: uuid.UUID(bytes=data),
    ExtTypes.DATETIME: lambda data: temporenc.unpackb(data).datetime(),
    ExtTypes.DECIMAL: lambda data: pickle.loads(data),
    ExtTypes.POSIX_PATH: lambda data: PosixPath(os.fsdecode(data)),
    ExtTypes.PURE_POSIX_PATH: lambda data: PurePosixPath(os.fsdecode(data)),
    ExtTypes.AUTO_DIRECTORY_PATH: lambda data: AutoDirectoryPath(os.fsdecode(data)),
    ExtTypes.ENUM: lambda data: pickle.loads(data),
    ExtTypes.RESOURCE_SLOT: lambda data: pickle.loads(data),
    ExtTypes.BACKENDAI_BINARY_SIZE: lambda data: pickle.loads(data),
    ExtTypes.IMAGE_REF: lambda data: pickle.loads(data),
}


class _Deserializer:
    def __init__(self, mapping: Optional[Mapping[int, ExtFunc]] = None):
        self._ext_hook: dict[int, ExtFunc] = {}
        mapping = mapping or {}
        self._ext_hook = {**mapping}
        for ext_type, func in _DEFAULT_EXT_HOOK.items():
            if ext_type not in self._ext_hook:
                self._ext_hook[ext_type] = func

    @property
    def ext_hook(self) -> Callable[[int, bytes], Any]:
        def _hook_callable(code: int, data: bytes) -> Any:
            if code in self._ext_hook:
                return self._ext_hook[code](data)
            return _msgpack.ExtType(code, data)

        return _hook_callable


uuid_to_str: Mapping[int, ExtFunc] = {ExtTypes.UUID: lambda data: str(uuid.UUID(bytes=data))}

DEFAULT_PACK_OPTS = {
    "use_bin_type": True,  # bytes -> bin type (default for Python 3)
    "strict_types": True,  # do not serialize subclasses using superclasses
    "default": _default,
}

DEFAULT_UNPACK_OPTS = {
    "raw": False,  # assume str as UTF-8 (default for Python 3)
    "strict_map_key": False,  # allow using UUID as map keys
    "use_list": False,  # array -> tuple
    "ext_hook": _Deserializer().ext_hook,
}


def packb(data: Any, **kwargs) -> bytes:
    opts = {**DEFAULT_PACK_OPTS, **kwargs}
    ret = _msgpack.packb(data, **opts)
    if ret is None:
        return b""
    return ret


def unpackb(
    packed: bytes, ext_hook_mapping: Optional[Mapping[int, ExtFunc]] = None, **kwargs
) -> Any:
    opts = {**DEFAULT_UNPACK_OPTS, **kwargs}
    if ext_hook_mapping is not None:
        opts["ext_hook"] = _Deserializer(ext_hook_mapping).ext_hook
    return _msgpack.unpackb(packed, **opts)
