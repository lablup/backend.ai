"""
An extension module to Trafaret which provides additional type checkers.
"""

import datetime
import enum
import ipaddress
import json
import os
import pwd
import random
import re
import uuid
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path as _Path
from pathlib import PurePath as _PurePath
from typing import (
    Any,
    Generic,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import dateutil.tz
from dateutil.relativedelta import relativedelta

try:
    import jwt

    jwt_available = True
except ImportError:
    jwt_available = False
import multidict
import trafaret as t
import yarl
from trafaret.base import TrafaretMeta, ensure_trafaret
from trafaret.lib import _empty

from .types import BinarySize as _BinarySize
from .types import HostPortPair as _HostPortPair
from .types import QuotaScopeID as _QuotaScopeID
from .types import RoundRobinState, RoundRobinStates
from .types import VFolderID as _VFolderID

__all__ = (
    "AliasedKey",
    "MultiKey",
    "BinarySize",
    "DelimiterSeperatedList",
    "StringList",
    "Enum",
    "JSONString",
    "PurePath",
    "Path",
    "IPNetwork",
    "IPAddress",
    "HostPortPair",
    "PortRange",
    "UserID",
    "GroupID",
    "UUID",
    "QuotaScopeID",
    "VFolderID",
    "TimeZone",
    "TimeDuration",
    "Slug",
    "URL",
)


class StringLengthMeta(TrafaretMeta):
    """
    A metaclass that makes string-like trafarets to have sliced min/max length indicator.
    """

    def __getitem__(cls, slice_):
        return cls(min_length=slice_.start, max_length=slice_.stop)


class AliasedKey(t.Key):
    """
    An extension to trafaret.Key which accepts multiple aliases of a single key.
    When successfully matched, the returned key name is the first one of the given aliases
    or the renamed key set via ``to_name()`` method or the ``>>`` operator.
    """

    def __init__(self, names: Sequence[str], **kwargs) -> None:
        super().__init__(names[0], **kwargs)
        self.names = names

    def __call__(self, data, context=None):
        for name in self.names:
            if name in data:
                key = name
                break
        else:
            key = None

        if key is None:  # not specified
            if self.default is not _empty:
                default = self.default() if callable(self.default) else self.default
                try:
                    result = self.trafaret(default, context=context)
                except t.DataError as inner_error:
                    yield self.get_name(), inner_error, self.names
                else:
                    yield self.get_name(), result, self.names
                return
            if not self.optional:
                yield self.get_name(), t.DataError(error="is required"), self.names
            # if optional, just bypass
        else:
            try:
                result = self.trafaret(data[key], context=context)
            except t.DataError as inner_error:
                yield key, inner_error, self.names
            else:
                yield self.get_name(), result, self.names


class MultiKey(t.Key):
    def get_data(self, data, default):
        if isinstance(data, (multidict.MultiDict, multidict.MultiDictProxy)):
            return data.getall(self.name, default)
        # fallback for plain dicts
        raw_value = data.get(self.name, default)
        if isinstance(raw_value, (List, Tuple)):
            # if plain dict already contains list of values, just return it.
            return raw_value
        # otherwise, wrap the value in a list.
        return [raw_value]


class BinarySize(t.Trafaret):
    def check_and_return(self, value: Any) -> Union[_BinarySize, Decimal]:
        try:
            if not isinstance(value, str):
                value = str(value)
            return _BinarySize.from_str(value)
        except ValueError:
            self._failure("value is not a valid binary size", value=value)


TListItem = TypeVar("TListItem")


class DelimiterSeperatedList(t.Trafaret, Generic[TListItem]):
    def __init__(
        self,
        trafaret: Type[t.Trafaret] | t.Trafaret,
        *,
        delimiter: str = ",",
        min_length: Optional[int] = None,
        empty_str_as_empty_list: bool = False,
    ) -> None:
        self.delimiter = delimiter
        self.empty_str_as_empty_list = empty_str_as_empty_list
        self.min_length = min_length
        self.trafaret = ensure_trafaret(trafaret)

    def check_and_return(self, value: Any) -> Sequence[TListItem]:
        try:
            if not isinstance(value, str):
                value = str(value)
            if self.empty_str_as_empty_list and not value:
                return []
            splited = value.split(self.delimiter)
            if self.min_length is not None and len(splited) < self.min_length:
                self._failure(
                    f"the number of items should be greater than {self.min_length}",
                    value=value,
                )
            return [self.trafaret.check_and_return(x) for x in splited]
        except ValueError:
            self._failure("value is not a string or not convertible to string", value=value)


class StringList(DelimiterSeperatedList[str]):
    def __init__(
        self,
        *,
        delimiter: str = ",",
        allow_blank: bool = False,
        min_length: Optional[int] = None,
        empty_str_as_empty_list: bool = False,
    ) -> None:
        super().__init__(
            t.String(allow_blank=allow_blank),
            delimiter=delimiter,
            min_length=min_length,
            empty_str_as_empty_list=empty_str_as_empty_list,
        )


T_enum = TypeVar("T_enum", bound=enum.Enum)


class Enum(t.Trafaret, Generic[T_enum]):
    def __init__(self, enum_cls: Type[T_enum], *, use_name: bool = False) -> None:
        self.enum_cls = enum_cls
        self.use_name = use_name

    def check_and_return(self, value: Any) -> T_enum:
        try:
            if self.use_name:
                return self.enum_cls[value]
            else:
                return self.enum_cls(value)
        except (KeyError, ValueError):
            self._failure(f"value is not a valid member of {self.enum_cls.__name__}", value=value)


class JSONString(t.Trafaret):
    def check_and_return(self, value: Any) -> dict:
        try:
            return json.loads(value)
        except (KeyError, ValueError):
            self._failure("value is not a valid JSON string", value=value)


class PurePath(t.Trafaret):
    def __init__(
        self,
        *,
        base_path: _PurePath = None,
        relative_only: bool = False,
    ) -> None:
        super().__init__()
        self._base_path = base_path
        self._relative_only = relative_only

    def check_and_return(self, value: Any) -> _PurePath:
        try:
            p = _PurePath(value)
        except (TypeError, ValueError):
            self._failure("cannot parse value as a path", value=value)

        if self._relative_only and p.is_absolute():
            self._failure("expected relative path but the value is absolute", value=value)
        if self._base_path is not None:
            try:
                p.relative_to(self._base_path)
            except ValueError:
                self._failure("value is not in the base path", value=value)
        return p


class Path(PurePath):
    def __init__(
        self,
        *,
        type: Literal["dir", "file"],
        base_path: _Path = None,
        auto_create: bool = False,
        allow_nonexisting: bool = False,
        allow_devnull: bool = False,
        relative_only: bool = False,
        resolve: bool = True,
    ) -> None:
        super().__init__(
            base_path=base_path,
            relative_only=relative_only,
        )
        self._type = type
        if auto_create and type != "dir":
            raise TypeError("Only directory paths can be set auto-created.")
        self._auto_create = auto_create
        self._allow_nonexisting = allow_nonexisting
        self._allow_devnull = allow_devnull
        self._resolve = resolve

    def check_and_return(self, value: Any) -> _Path:
        try:
            p = _Path(value).resolve() if self._resolve else _Path(value)
        except (TypeError, ValueError):
            self._failure("cannot parse value as a path", value=value)
        if self._relative_only and p.is_absolute():
            self._failure("expected relative path but the value is absolute", value=value)
        if self._base_path is not None:
            try:
                _base_path = _Path(self._base_path).resolve() if self._resolve else self._base_path
                p.relative_to(_base_path)
            except ValueError:
                self._failure("value is not in the base path", value=value)
        if self._type == "dir":
            if self._auto_create:
                p.mkdir(parents=True, exist_ok=True)
            if not self._allow_nonexisting and not p.is_dir():
                self._failure("value is not a directory", value=value)
        elif self._type == "file":
            if not self._allow_devnull and str(p) == os.devnull:
                # it may be not a regular file but a char-device.
                return p
            if not self._allow_nonexisting and not p.is_file():
                self._failure("value is not a regular file", value=value)
        return p


class IPNetwork(t.Trafaret):
    def check_and_return(self, value: Any) -> ipaddress._BaseNetwork:
        try:
            return ipaddress.ip_network(value)
        except ValueError:
            self._failure("Invalid IP network format", value=value)


class IPAddress(t.Trafaret):
    def check_and_return(self, value: Any) -> ipaddress._BaseAddress:
        try:
            return ipaddress.ip_address(value)
        except ValueError:
            self._failure("Invalid IP address format", value=value)


class HostPortPair(t.Trafaret):
    def __init__(self, *, allow_blank_host: bool = False) -> None:
        super().__init__()
        self._allow_blank_host = allow_blank_host

    def check_and_return(self, value: Any) -> Tuple[ipaddress._BaseAddress, int]:
        host: str | ipaddress._BaseAddress
        if isinstance(value, str):
            pair = value.rsplit(":", maxsplit=1)
            if len(pair) == 1:
                self._failure("value as string must contain both address and number", value=value)
            host, port = pair[0], pair[1]
        elif isinstance(value, Sequence):
            if len(value) != 2:
                self._failure(
                    "value as array must contain only two values for address and number",
                    value=value,
                )
            host, port = value[0], value[1]
        elif isinstance(value, Mapping):
            try:
                host, port = value["host"], value["port"]
            except KeyError:
                self._failure('value as map must contain "host" and "port" keys', value=value)
        else:
            self._failure("urecognized value type", value=value)
        try:
            if isinstance(host, str):
                host = ipaddress.ip_address(host.strip("[]"))
            elif isinstance(host, ipaddress._BaseAddress):
                pass
        except ValueError:
            pass  # just treat as a string hostname
        if not self._allow_blank_host and not host:
            self._failure("value has empty host", value=value)
        try:
            port = t.ToInt[1:65535].check(port)
        except t.DataError:
            self._failure("port number must be between 1 and 65535", value=value)
        return _HostPortPair(host, port)


class PortRange(t.Trafaret):
    def check_and_return(self, value: Any) -> Tuple[int, int]:
        if isinstance(value, str):
            try:
                value = tuple(map(int, value.split("-")))
            except (TypeError, ValueError):
                self._failure(
                    "value as string should be a hyphen-separated pair of integers", value=value
                )
        elif isinstance(value, Sequence):
            if len(value) != 2:
                self._failure("value as array must contain only two values", value=value)
        else:
            self._failure("urecognized value type", value=value)
        try:
            min_port = t.Int[1:65535].check(value[0])
            max_port = t.Int[1:65535].check(value[1])
        except t.DataError:
            self._failure("each value must be a valid port number", value=value)
        if not (min_port < max_port):
            self._failure("first value must be less than second value", value=value)
        return min_port, max_port


class UserID(t.Trafaret):
    def __init__(self, *, default_uid: int = None) -> None:
        super().__init__()
        self._default_uid = default_uid

    def check_and_return(self, value: Any) -> int:
        if value is None:
            if self._default_uid is not None:
                return self._default_uid
            else:
                return os.getuid()
        elif isinstance(value, int):
            if value == -1:
                return os.getuid()
        elif isinstance(value, str):
            if not value:
                if self._default_uid is not None:
                    return self._default_uid
                else:
                    return os.getuid()
            try:
                value = int(value)
            except ValueError:
                try:
                    return pwd.getpwnam(value).pw_uid
                except KeyError:
                    self._failure("no such user in system", value=value)
            else:
                return self.check_and_return(value)
        else:
            self._failure("value must be either int or str", value=value)
        return value


class GroupID(t.Trafaret):
    def __init__(self, *, default_gid: int = None) -> None:
        super().__init__()
        self._default_gid = default_gid

    def check_and_return(self, value: Any) -> int:
        if value is None:
            if self._default_gid is not None:
                return self._default_gid
            else:
                return os.getgid()
        elif isinstance(value, int):
            if value == -1:
                return os.getgid()
        elif isinstance(value, str):
            if not value:
                if self._default_gid is not None:
                    return self._default_gid
                else:
                    return os.getgid()
            try:
                value = int(value)
            except ValueError:
                try:
                    return pwd.getpwnam(value).pw_gid
                except KeyError:
                    self._failure("no such group in system", value=value)
            else:
                return self.check_and_return(value)
        else:
            self._failure("value must be either int or str", value=value)
        return value


class UUID(t.Trafaret):
    def check_and_return(self, value: Any) -> uuid.UUID:
        try:
            if isinstance(value, uuid.UUID):
                return value
            if isinstance(value, str):
                return uuid.UUID(value)
            elif isinstance(value, bytes):
                return uuid.UUID(bytes=value)
            else:
                self._failure("value must be string or bytes", value=value)
        except ValueError:
            self._failure("cannot convert value to UUID", value=value)


class QuotaScopeID(t.Trafaret):
    regex = r"^[A-Za-z0-9]+(?:[_-][A-Za-z0-9]+)*:[A-Za-z0-9]+(?:[_-][A-Za-z0-9]+)*$"

    def check_and_return(self, value: Any) -> _QuotaScopeID:
        return _QuotaScopeID.parse(t.Regexp(self.regex).check(value))


class VFolderID(t.Trafaret):
    def check_and_return(self, value: Any) -> _VFolderID:
        tuple_t = t.Tuple(QuotaScopeID(), UUID())
        match value:
            case str():
                pieces = value.partition("/")
                if len(pieces[2]) == 0:  # for old vFolder ID without quota scope ID
                    converted = (None, UUID().check(pieces[0]))
                else:
                    converted = tuple_t.check((pieces[0], pieces[2]))
            case tuple():
                converted = tuple_t.check(value)
            case _:
                self._failure("cannot convert value to VFolderID", value=value)
        return _VFolderID(
            quota_scope_id=converted[0],
            folder_id=converted[1],
        )


class TimeZone(t.Trafaret):
    def check_and_return(self, value: Any) -> datetime.tzinfo:
        if not isinstance(value, str):
            self._failure("value must be string", value=value)
        tz = dateutil.tz.gettz(value)
        if tz is None:
            self._failure("value is not a known timezone", value=value)
        return tz


class TimeDuration(t.Trafaret):
    """
    Represent the relative difference between two datetime objects,
    parsed from human-readable time duration expression strings.

    If you specify years or months, it returns an
    :class:`dateutil.relativedelta.relativedelta` instance
    which keeps the human-friendly year and month calculation
    considering leap years and monthly day count differences,
    instead of simply multiplying 365 days to the value of years.
    Otherwise, it returns the stdlib's :class:`datetime.timedelta`
    instance.

    Example:
    >>> t = datetime(2020, 2, 29)
    >>> t + check_and_return("1yr")
    datetime.datetime(2021, 2, 28, 0, 0)
    >>> t + check_and_return("2yr")
    datetime.datetime(2022, 2, 28, 0, 0)
    >>> t + check_and_return("3yr")
    datetime.datetime(2023, 2, 28, 0, 0)
    >>> t + check_and_return("4yr")
    datetime.datetime(2024, 2, 29, 0, 0)  # preserves the same day of month
    """

    def __init__(self, *, allow_negative: bool = False) -> None:
        self._allow_negative = allow_negative

    def check_and_return(self, value: Any) -> Union[datetime.timedelta, relativedelta]:
        if not isinstance(value, (int, float, str)):
            self._failure("value must be a number or string", value=value)
        if isinstance(value, (int, float)):
            return datetime.timedelta(seconds=value)
        assert isinstance(value, str)
        if len(value) == 0:
            self._failure("value must not be empty", value=value)
        try:
            unit = value[-1]
            if unit.isdigit():
                t = float(value)
                if not self._allow_negative and t < 0:
                    self._failure("value must be positive", value=value)
                return datetime.timedelta(seconds=t)
            elif value[-2:].isalpha():
                t = int(value[:-2])
                if not self._allow_negative and t < 0:
                    self._failure("value must be positive", value=value)
                if value[-2:] == "yr":
                    return relativedelta(years=t)
                elif value[-2:] == "mo":
                    return relativedelta(months=t)
                else:
                    self._failure("value is not a known time duration", value=value)
            else:
                t = float(value[:-1])
                if not self._allow_negative and t < 0:
                    self._failure("value must be positive", value=value)
                if value[-1] == "w":
                    return datetime.timedelta(weeks=t)
                elif value[-1] == "d":
                    return datetime.timedelta(days=t)
                elif value[-1] == "h":
                    return datetime.timedelta(hours=t)
                elif value[-1] == "m":
                    return datetime.timedelta(minutes=t)
                elif value[-1] == "s":
                    return datetime.timedelta(seconds=t)
                else:
                    self._failure("value is not a known time duration", value=value)
        except ValueError:
            self._failure(f"invalid numeric literal: {value[:-1]}", value=value)


class Slug(t.Trafaret, metaclass=StringLengthMeta):
    _rx_slug = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$")

    def __init__(
        self,
        *,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        allow_dot: bool = False,
    ) -> None:
        super().__init__()
        self._allow_dot = allow_dot
        if min_length is not None and min_length < 0:
            raise TypeError("min_length must be larger than or equal to zero.")
        if max_length is not None and max_length < 0:
            raise TypeError("max_length must be larger than or equal to zero.")
        if max_length is not None and min_length is not None and min_length > max_length:
            raise TypeError("min_length must be less than or equal to max_length when both set.")
        self._min_length = min_length
        self._max_length = max_length

    def check_and_return(self, value: Any) -> str:
        if isinstance(value, str):
            if self._min_length is not None and len(value) < self._min_length:
                self._failure(f"value is too short (min length {self._min_length})", value=value)
            if self._max_length is not None and len(value) > self._max_length:
                self._failure(f"value is too long (max length {self._max_length})", value=value)
            if self._allow_dot and value.startswith("."):
                checked_value = value[1:]
            else:
                checked_value = value
            m = type(self)._rx_slug.search(checked_value)
            if not m:
                self._failure("value must be a valid slug.", value=value)
        else:
            self._failure("value must be a string", value=value)
        return value


if jwt_available:

    class JsonWebToken(t.Trafaret):
        default_algorithms = ["HS256"]

        def __init__(
            self,
            *,
            secret: str,
            inner_iv: t.Trafaret = None,
            algorithms: list[str] = default_algorithms,
        ) -> None:
            self.secret = secret
            self.algorithms = algorithms
            self.inner_iv = inner_iv

        def check_and_return(self, value: Any) -> Mapping[str, Any]:
            try:
                token_data = jwt.decode(value, self.secret, algorithms=self.algorithms)
                if self.inner_iv is not None:
                    return self.inner_iv.check(token_data)
                return token_data
            except jwt.PyJWTError as e:
                self._failure(f"cannot decode the given value as JWT: {e}", value=value)


class URL(t.Trafaret):
    def __init__(
        self,
        *,
        scheme_required: bool = True,
    ) -> None:
        self.scheme_required = scheme_required

    def check_and_return(self, value: Any) -> yarl.URL:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        try:
            parsed_url = yarl.URL(value)
            if self.scheme_required:
                parsed_url.origin()
        except (ValueError, TypeError) as e:
            self._failure(repr(e), value=value)
        else:
            return parsed_url


class ToSet(t.Trafaret):
    def check_and_return(self, value: Any) -> set:
        if isinstance(value, Iterable):
            return set(value)
        else:
            self._failure("value must be Iterable")


class Delay(t.Trafaret):
    """
    Convert a float or a tuple of 2 floats into a random generated float value
    to use in time.sleep() or asyncio.sleep()
    """

    def check_and_return(self, value: Any) -> float:
        match value:
            case float() | int():
                return float(value)
            case (a, b):
                return random.uniform(a, b)
            case None:
                return 0
            case _:
                self._failure(f"Value must be (float, tuple of float or None), not {type(value)}.")


class RoundRobinStatesJSONString(t.Trafaret):
    def check_and_return(self, value: Any) -> RoundRobinStates:
        try:
            rr_states_dict: dict[str, dict[str, dict[str, Any]]] = json.loads(value)
        except (KeyError, ValueError, json.decoder.JSONDecodeError):
            self._failure(
                f"Expected valid JSON string, got `{value}`. RoundRobinStatesJSONString should"
                " be a valid JSON string",
                value=value,
            )

        rr_states: RoundRobinStates = {}
        for resource_group, arch_rr_states_dict in rr_states_dict.items():
            rr_states[resource_group] = {}
            for arch, rr_state_dict in arch_rr_states_dict.items():
                if "next_index" not in rr_state_dict or "schedulable_group_id" not in rr_state_dict:
                    self._failure("Invalid roundrobin states")
                rr_states[resource_group][arch] = RoundRobinState.from_json(rr_state_dict)

        return rr_states
