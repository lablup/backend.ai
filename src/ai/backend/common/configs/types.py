import datetime
import ipaddress
from collections.abc import Mapping
from datetime import timedelta, tzinfo
from typing import Any, ClassVar, Sequence

from dateutil import tz
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, RootModel, model_validator

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


TimeDelta = timedelta | relativedelta


class TimeDuration(RootModel[TimeDelta]):
    root: TimeDelta
    _allow_negative: ClassVar[bool] = False

    @model_validator(mode="before")
    @classmethod
    def _parse(cls, value: Any) -> Any:
        if isinstance(value, (relativedelta, datetime.timedelta)):
            return value

        if isinstance(value, (int, float)):
            return datetime.timedelta(seconds=value)

        if not isinstance(value, str):
            raise ValueError("value must be a number or string")
        if len(value) == 0:
            raise ValueError("value must not be empty")

        try:
            unit = value[-1]
            if unit.isdigit():
                t = float(value)
                if not cls._allow_negative and t < 0:
                    raise ValueError(f"value {value} must be positive")
                return datetime.timedelta(seconds=t)

            elif value[-2:].isalpha():
                t = int(value[:-2])
                if not cls._allow_negative and t < 0:
                    raise ValueError(f"value {value} must be positive")
                if value[-2:] == "yr":
                    return relativedelta(years=t)
                elif value[-2:] == "mo":
                    return relativedelta(months=t)
                else:
                    raise ValueError(f"value {value} is not a known time duration")

            else:
                t = float(value[:-1])
                if not cls._allow_negative and t < 0:
                    raise ValueError(f"value {value} must be positive")
                match value[-1]:
                    case "w":
                        return datetime.timedelta(weeks=t)
                    case "d":
                        return datetime.timedelta(days=t)
                    case "h":
                        return datetime.timedelta(hours=t)
                    case "m":
                        return datetime.timedelta(minutes=t)
                    case "s":
                        return datetime.timedelta(seconds=t)
                    case _:
                        raise ValueError(f"value {value} is not a known time duration")

        except ValueError:
            raise ValueError(f"invalid numeric literal: {value[:-1]}")


class TimeZone(RootModel[tzinfo]):
    root: tzinfo

    @model_validator(mode="before")
    @classmethod
    def _parse(cls, value: Any) -> Any:
        if isinstance(value, tzinfo):
            return value
        if isinstance(value, str):
            tzobj = tz.gettz(value)
            if tzobj is None:
                raise ValueError(f"value is not a known timezone: {value!r}")
            return tzobj
        raise TypeError("value must be string or tzinfo")
