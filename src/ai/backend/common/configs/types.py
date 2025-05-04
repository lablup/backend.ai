import ipaddress
from collections.abc import Mapping
from datetime import tzinfo
from typing import Annotated, Any, ClassVar, Sequence

from dateutil import tz
from pydantic import BaseModel, Field, PlainValidator, model_validator

from ai.backend.common.types import HostPortPair as LegacyHostPortPair


class HostPortPair(BaseModel):
    host: str = Field(
        description="""
        Host address of the service.
        Can be a hostname, IP address, or special addresses like 0.0.0.0 to bind to all interfaces.
        """,
        examples=["127.0.0.1"],
    )
    port: int = Field(
        ge=1,
        le=65535,
        description="""
        Port number of the service.
        Must be between 1 and 65535.
        Ports below 1024 require root/admin privileges.
        """,
        examples=[8080],
    )

    _allow_blank_host: ClassVar[bool] = True

    @model_validator(mode="before")
    @classmethod
    def _parse(cls, value: Any) -> Any:
        host: str | ipaddress._BaseAddress
        port: str | int

        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            pair = value.rsplit(":", maxsplit=1)
            if len(pair) == 1:
                raise ValueError("value as string must contain both address and number")
            host = pair[0]
            port = pair[1]

        elif isinstance(value, Sequence):
            if len(value) != 2:
                raise ValueError(
                    "value as array must contain only two values for address and number"
                )
            host, port = value

        elif isinstance(value, Mapping):
            try:
                host, port = value["host"], value["port"]
            except KeyError:
                raise ValueError('value as map must contain "host" and "port" keys')

        else:
            raise TypeError("unrecognized value type")

        try:
            if isinstance(host, str):
                host = str(ipaddress.ip_address(host.strip("[]")))
        except ValueError:
            pass

        if not cls._allow_blank_host and not host:
            raise ValueError("value has empty host")

        try:
            port = int(port)
        except (TypeError, ValueError):
            raise ValueError("port number must be an integer")
        if not (1 <= port <= 65535):
            raise ValueError("port number must be between 1 and 65535")

        return {"host": str(host), "port": port}

    def __getitem__(self, *args) -> int | str:
        if args[0] == 0:
            return self.host
        elif args[0] == 1:
            return self.port
        else:
            raise KeyError(*args)

    def to_trafaret(self) -> LegacyHostPortPair:
        return LegacyHostPortPair(host=self.host, port=self.port)


def _parse_to_tzinfo(value: Any) -> tzinfo:
    if isinstance(value, tzinfo):
        return value
    if isinstance(value, str):
        tzobj = tz.gettz(value)
        if tzobj is None:
            raise ValueError(f"value is not a known timezone: {value!r}")
        return tzobj
    raise TypeError("value must be string or tzinfo")


TimeZone = Annotated[
    tzinfo,
    PlainValidator(_parse_to_tzinfo),
]
