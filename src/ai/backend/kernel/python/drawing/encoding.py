from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

import msgpack

if TYPE_CHECKING:
    from collections.abc import Sequence


def encode_commands(cmdlist: Sequence[Any]) -> str:
    bindata = msgpack.packb(cmdlist, use_bin_type=True)
    return base64.b64encode(bindata).decode("ascii")


def decode_commands(data: str | bytes) -> list[Any]:
    bindata = base64.b64decode(data)
    result: list[Any] = msgpack.unpackb(bindata, raw=False)
    return result
