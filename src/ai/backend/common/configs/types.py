import ipaddress
from datetime import timedelta, tzinfo
from typing import Annotated, Any, Mapping, Sequence

from dateutil import tz
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, PlainValidator

from ai.backend.common.types import HostPortPair as LegacyHostPortPair


class _HostPortPair(BaseModel):
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

    def __getitem__(self, *args) -> int | str:
        if args[0] == 0:
            return self.host
        elif args[0] == 1:
            return self.port
        else:
            raise KeyError(*args)

    # TODO: Remove this after all pydantic migration jobs done
    def to_trafaret(self) -> LegacyHostPortPair:
        return LegacyHostPortPair(
            host=self.host,
            port=self.port,
        )


# TODO: allow_blank_host가 False인 HostPortPair 타입을 하나 더 만들어야 할지?
def _parse_host_port_pair(value: Any, *, allow_blank_host: bool = True) -> _HostPortPair:
    if isinstance(value, _HostPortPair):
        return value

    if isinstance(value, str):
        host: str | ipaddress._BaseAddress
        port: str | int

        pair = value.rsplit(":", maxsplit=1)
        if len(pair) == 1:
            raise ValueError("value as string must contain both address and number")
        host = pair[0]
        port = pair[1]
    elif isinstance(value, Sequence):
        if len(value) != 2:
            raise ValueError("value as array must contain only two values for address and number")
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
        elif isinstance(host, ipaddress._BaseAddress):
            pass
    except ValueError:
        pass

    if not allow_blank_host and not host:
        raise ValueError("value has empty host")

    try:
        port = int(port)
    except (TypeError, ValueError):
        raise ValueError("port number must be between 1 and 65535")
    if not (1 <= port <= 65535):
        raise ValueError("port number must be between 1 and 65535")

    return _HostPortPair(host=str(host), port=port)


HostPortPair = Annotated[_HostPortPair, PlainValidator(_parse_host_port_pair)]


TimeDelta = timedelta | relativedelta


def _parse_time_duration(v: Any) -> TimeDelta:
    if isinstance(v, (relativedelta, timedelta)):
        return v

    if isinstance(v, (int, float)):
        if v < 0:
            raise ValueError("value must be positive")
        return timedelta(seconds=v)

    if not isinstance(v, str) or len(v) == 0:
        raise ValueError("value must be a number or string")

    try:
        if v[-2:].isalpha():
            num_part, unit = v[:-2], v[-2:].lower()
            if not num_part:
                raise ValueError("value must not be empty")
            t = int(num_part)
            if t < 0:
                raise ValueError("value must be positive")
            if unit == "yr":
                return relativedelta(years=t)
            if unit == "mo":
                return relativedelta(months=t)
            raise ValueError("value is not a known time duration")

        unit = v[-1].lower()
        num_part = v[:-1] if unit.isalpha() else v
        seconds_value: float = float(num_part)
        if seconds_value < 0:
            raise ValueError("value must be positive")

        if not unit.isalpha():
            return timedelta(seconds=seconds_value)
        if unit == "w":
            return timedelta(weeks=seconds_value)
        if unit == "d":
            return timedelta(days=seconds_value)
        if unit == "h":
            return timedelta(hours=seconds_value)
        if unit == "m":
            return timedelta(minutes=seconds_value)
        if unit == "s":
            return timedelta(seconds=seconds_value)

        raise ValueError("value is not a known time duration")
    except ValueError as exc:
        raise ValueError(str(exc)) from None


TimeDuration = Annotated[timedelta, PlainValidator(_parse_time_duration)]


def _parse_to_tzinfo(v: Any) -> tzinfo:
    if isinstance(v, tzinfo):
        return v
    if isinstance(v, str):
        tzobj = tz.gettz(v)
        if tzobj is None:
            raise ValueError(f"unknown timezone: {v!r}")
        return tzobj
    raise TypeError("timezone must be str or tzinfo")


TimeZone = Annotated[
    tzinfo,
    PlainValidator(_parse_to_tzinfo),
]
