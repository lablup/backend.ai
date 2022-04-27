'''
Wrapper of msgpack-python with good defaults.
'''

from typing import Any

import msgpack as _msgpack


def packb(data: Any, **kwargs) -> bytes:
    opts = {"use_bin_type": True, **kwargs}
    return _msgpack.packb(data, **opts)


def unpackb(packed: bytes, **kwargs) -> Any:
    opts = {"raw": False, "use_list": False, **kwargs}
    return _msgpack.unpackb(packed, **opts)
