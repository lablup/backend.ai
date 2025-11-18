import datetime
import ipaddress
import os
import pwd
from collections.abc import Mapping, Sequence
from datetime import tzinfo
from pathlib import Path
from typing import Annotated, Any, ClassVar, Final, Optional, TypeAlias, TypeVar

from dateutil import tz
from dateutil.relativedelta import relativedelta
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    PlainValidator,
    TypeAdapter,
    ValidationError,
    WithJsonSchema,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

from ai.backend.common.types import HostPortPair as LegacyHostPortPair

from .defs import (
    API_VFOLDER_LENGTH_LIMIT,
    MODEL_VFOLDER_LENGTH_LIMIT,
    RESERVED_VFOLDER_PATTERNS,
    RESERVED_VFOLDERS,
)

TVariousDelta: TypeAlias = datetime.timedelta | relativedelta


class _TimeDurationPydanticAnnotation:
    allow_negative = False

    @classmethod
    def time_duration_validator(
        cls,
        value: int | float | str,
    ) -> TVariousDelta:
        assert isinstance(value, (int, float, str)), "value must be a number or string"
        if isinstance(value, (int, float)):
            return datetime.timedelta(seconds=value)
        assert len(value) > 0, "value must not be empty"

        try:
            unit = value[-1]
            if unit.isdigit():
                t = float(value)
                assert cls.allow_negative or t >= 0, "value must be positive"
                return datetime.timedelta(seconds=t)
            elif value[-2:].isalpha():
                t = int(value[:-2])
                assert cls.allow_negative or t >= 0, "value must be positive"
                match value[-2:]:
                    case "yr":
                        return relativedelta(years=t)
                    case "mo":
                        return relativedelta(months=t)
                    case _:
                        raise AssertionError("value is not a known time duration")
            else:
                t = float(value[:-1])
                assert cls.allow_negative or t >= 0, "value must be positive"
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
                        raise AssertionError("value is not a known time duration")
        except ValueError:
            raise AssertionError(f"invalid numeric literal: {value[:-1]}")

    @classmethod
    def time_duration_serializer(cls, value: TVariousDelta) -> float | str:
        match value:
            case datetime.timedelta():
                return value.total_seconds()
            case relativedelta():
                # just like the deserializer, serializing relativedelta is only supported when year or month (not both) is supplied
                # years or months being normalized is not considered as a valid case since relativedelta does not allow fraction of years or months as an input
                assert not (value.years and value.months), (
                    "Serializing relativedelta with both years and months contained is not supported"
                )
                assert value.years or value.months, (
                    "Serialization is supported only for months or years field"
                )
                if value.years:
                    return f"{value.years}yr"
                elif value.months:
                    return f"{value.months}mo"
                else:
                    raise AssertionError("Should not reach here")
            case _:
                raise AssertionError("Not a valid type")

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = core_schema.chain_schema([
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.float_schema(),
                core_schema.str_schema(),
            ]),
            core_schema.no_info_plain_validator_function(cls.time_duration_validator),
        ])

        return core_schema.json_or_python_schema(
            json_schema=schema,
            python_schema=core_schema.union_schema([
                # check if it's an instance first before doing any further work
                core_schema.union_schema([
                    core_schema.is_instance_schema(datetime.timedelta),
                    core_schema.is_instance_schema(relativedelta),
                ]),
                schema,
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.time_duration_serializer
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.float_schema(),
                core_schema.str_schema(),
            ])
        )


class _NaiveTimeDurationPydanticAnnotation(_TimeDurationPydanticAnnotation):
    allow_negative = True


TimeDuration = Annotated[
    TVariousDelta,
    _TimeDurationPydanticAnnotation,
]
"""Time duration validator accepting only non-negative value"""


NaiveTimeDuration = Annotated[TVariousDelta, _NaiveTimeDurationPydanticAnnotation]
"""Time duration validator which also accepts negative value"""

SESSION_NAME_MAX_LENGTH: Final[int] = 24


def _vfolder_name_validator(name: str) -> str:
    f"""
    Although the length constraint of the `vfolders.name` column is {MODEL_VFOLDER_LENGTH_LIMIT},
    we limit the length to {API_VFOLDER_LENGTH_LIMIT} in the create/rename API
    because we append a timestamp of deletion to the name when VFolders are deleted.
    """
    if (name_len := len(name)) > API_VFOLDER_LENGTH_LIMIT:
        raise AssertionError(
            f"The length of VFolder name should be shorter than {API_VFOLDER_LENGTH_LIMIT}. (len: {name_len})"
        )
    if name in RESERVED_VFOLDERS:
        raise AssertionError(f"VFolder name '{name}' is reserved for internal operations")
    for pattern in RESERVED_VFOLDER_PATTERNS:
        if pattern.match(name):
            raise AssertionError(
                f"VFolder name '{name}' matches a reserved pattern (pattern: {pattern})"
            )
    return name


VFolderName = Annotated[str, AfterValidator(_vfolder_name_validator)]


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

    model_config = ConfigDict(frozen=True)

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

    def to_legacy(self) -> LegacyHostPortPair:
        return LegacyHostPortPair(host=self.host, port=self.port)

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        return self.address

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


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
    WithJsonSchema(
        core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.str_schema(),
        ),
    ),
]


class AutoDirectoryPath(DirectoryPath):
    """`DirectoryPath` that silently creates the directory if it is missing."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def ensure_exists_and_resolve(value: Any) -> Path:
            p = Path(value).expanduser()

            if not p.is_absolute():
                p = Path.cwd() / p

            p.mkdir(parents=True, exist_ok=True)
            return p.resolve()

        return core_schema.chain_schema([
            core_schema.no_info_plain_validator_function(ensure_exists_and_resolve),
            handler(DirectoryPath),
        ])

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(
            core_schema.str_schema(),
        )


class UserID(int):
    _default_uid: Optional[int] = None

    @classmethod
    def check_and_return(cls, value: Any) -> int:
        if value is None:
            if cls._default_uid is not None:
                return cls._default_uid
            else:
                return os.getuid()
        elif isinstance(value, int):
            if value == -1:
                return os.getuid()
        elif isinstance(value, str):
            if not value:
                if cls._default_uid is not None:
                    return cls._default_uid
                else:
                    return os.getuid()
            try:
                value = int(value)
            except ValueError:
                try:
                    return pwd.getpwnam(value).pw_uid
                except KeyError:
                    raise ValueError(f"no such user {value} in system")
            else:
                return cls.check_and_return(value)
        else:
            raise ValueError("value must be either int or str")
        return value

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def _validate(value: Any) -> "UserID":
            uid_int = cls.check_and_return(value)
            return cls(uid_int)

        return core_schema.no_info_plain_validator_function(_validate)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(
            core_schema.str_schema(),
        )


class GroupID(int):
    _default_gid: Optional[int] = None

    @classmethod
    def check_and_return(cls, value: Any) -> int:
        if value is None:
            if cls._default_gid is not None:
                return cls._default_gid
            else:
                return os.getgid()
        elif isinstance(value, int):
            if value == -1:
                return os.getgid()
        elif isinstance(value, str):
            if not value:
                if cls._default_gid is not None:
                    return cls._default_gid
                else:
                    return os.getgid()
            try:
                value = int(value)
            except ValueError:
                try:
                    return pwd.getpwnam(value).pw_gid
                except KeyError:
                    raise ValueError(f"no such group {value!r} in system")
            else:
                return cls.check_and_return(value)
        else:
            raise ValueError("value must be either int or str")
        return value

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def _validate(value: Any) -> "GroupID":
            gid_int = cls.check_and_return(value)
            return cls(gid_int)

        return core_schema.no_info_plain_validator_function(_validate)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(
            core_schema.str_schema(),
        )


TItem = TypeVar("TItem")


class DelimiterSeparatedList(list[TItem]):
    delimiter: str = ","
    min_length: Optional[int] = None
    empty_str_as_empty_list: bool = False

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def _validate(value: Any, _info: core_schema.ValidationInfo) -> list[TItem]:
            item_type = getattr(cls, "__args__", (str,))[0]
            item_adapter = TypeAdapter(item_type)

            if not isinstance(value, str):
                value = str(value)
            if cls.empty_str_as_empty_list and value == "":
                return cls([])
            items = value.split(cls.delimiter)

            if cls.min_length is not None and len(items) < cls.min_length:
                raise ValueError(f"the number of items should be greater than {cls.min_length}")

            try:
                return cls([item_adapter.validate_python(x) for x in items])
            except ValidationError as e:
                raise ValueError(str(e))

        def _serialize(val: Sequence[Any]):
            return cls.delimiter.join(str(x) for x in val)

        return core_schema.with_info_plain_validator_function(
            _validate,
            serialization=core_schema.plain_serializer_function_ser_schema(_serialize),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(
            core_schema.str_schema(),
        )


class CommaSeparatedStrList(DelimiterSeparatedList[str]):
    delimiter = ","
    min_length = None
