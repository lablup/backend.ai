import datetime
import json
import uuid
from typing import Any, Optional, Protocol, Union

import orjson


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)


def load_json(s: Union[bytes, bytearray, memoryview, str]) -> Any:
    """
    Loads a JSON string into a Python object.
    """
    return orjson.loads(s)


class AsyncReader(Protocol):
    async def read(self) -> bytes:
        pass


async def read_json(reader: AsyncReader) -> Any:
    """
    Reads a JSON body from an asynchronous reader.
    """
    data = await reader.read()
    return load_json(data)


def dump_json_str(obj: Any, option: Optional[int] = None) -> str:
    """
    Dumps the given object into a JSON string.
    """
    return orjson.dumps(obj, option=option).decode("utf-8")


def dump_json(obj: Any, option: Optional[int] = None) -> bytes:
    """
    Dumps the given object into a JSON bytes.
    """
    return orjson.dumps(obj, option=option)


def pretty_json_str(obj: Any) -> str:
    """
    Dumps the given object into a pretty JSON string.
    """
    return dump_json_str(obj, orjson.OPT_INDENT_2)


def pretty_json(obj: Any) -> bytes:
    """ "
    Dumps the given object into a pretty JSON bytes.
    """
    return dump_json(obj, orjson.OPT_INDENT_2)
