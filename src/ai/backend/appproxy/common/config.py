import enum
import os
import pwd
import types
import typing
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ByteSize,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticUndefined, core_schema

from .types import DigestModType

# FIXME: merge majority of common definitions to ai.backend.common when ready


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


class PermitHashConfig(BaseSchema):
    secret: Annotated[
        bytes,
        Field(
            description="Secret string used for creating permit hash.",
            examples=["50M3G00DL00KING53CR3T"],
        ),
    ]
    digest_mod: Annotated[
        DigestModType, Field(description="Hash digest method to use.", default=DigestModType.SHA256)
    ]


class HostPortPair(BaseSchema):
    host: Annotated[str, Field(examples=["127.0.0.1"])]
    port: Annotated[int, Field(gt=0, lt=65536, examples=[8201])]

    @property
    def host_set_with_protocol(self) -> bool:
        for protocol in ("http://", "https://"):
            if self.host.startswith(protocol):
                return True
        return False

    def __repr__(self) -> str:
        return f"{self.host}:{self.port}"

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, *args) -> int | str:
        if args[0] == 0:
            return self.host
        elif args[0] == 1:
            return self.port
        else:
            raise KeyError(*args)


class RedisHelperConfig(BaseSchema):
    socket_timeout: Annotated[float, Field(default=5.0)]
    socket_connect_timeout: Annotated[float, Field(default=2.0)]
    reconnect_poll_timeout: Annotated[float, Field(default=0.3)]


class RedisConfig(BaseSchema):
    addr: Annotated[
        HostPortPair | None,
        Field(
            default=None,
            description="Address and port number of redis server.",
            examples=[HostPortPair(host="127.0.0.1", port=8111)],
        ),
    ]
    sentinel: Annotated[
        list[HostPortPair] | None,
        Field(
            default=None,
            description="List of address/port pair of sentinel servers.",
            examples=[
                [
                    HostPortPair(host="127.0.0.1", port=9503),
                    HostPortPair(host="127.0.0.1", port=9504),
                    HostPortPair(host="127.0.0.1", port=9505),
                ]
            ],
        ),
    ]
    service_name: Annotated[
        str | None, Field(default=None, description="Redis service name.", examples=["bai-service"])
    ]
    password: Annotated[
        str | None, Field(default=None, description="Redis password.", examples=["P@ssw0rd!"])
    ]
    redis_helper_config: Annotated[RedisHelperConfig, Field(default=RedisHelperConfig())]

    def to_dict(self) -> dict[str, Any]:
        base = self.model_dump()
        if self.addr:
            base["addr"] = f"{self.addr.host}:{self.addr.port}"
        if self.sentinel:
            base["sentinel"] = ",".join([f"{r.host}:{r.port}" for r in self.sentinel])
        return base


@dataclass
class UserID:
    default_uid: int | None = None

    @classmethod
    def uid_validator(
        cls,
        value: int | str | None,
    ) -> int:
        if value is None:
            assert cls.default_uid, "value is None but default_uid not provided"
            return cls.default_uid
        assert isinstance(value, (int, str)), "value must be an integer"
        match value:
            case int():
                if value == -1:
                    return os.getuid()
                else:
                    return value
            case str():
                try:
                    _value = int(value)
                    if _value == -1:
                        return os.getuid()
                    else:
                        return _value
                except ValueError:
                    try:
                        return pwd.getpwnam(value).pw_uid
                    except KeyError:
                        assert False, f"no such user {value} in system"

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = core_schema.chain_schema([
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ]),
            core_schema.no_info_plain_validator_function(cls.uid_validator),
        ])

        return core_schema.json_or_python_schema(
            json_schema=schema,
            python_schema=core_schema.union_schema([
                # check if it's an instance first before doing any further work
                core_schema.union_schema([
                    core_schema.is_instance_schema(int),
                    core_schema.is_instance_schema(str),
                ]),
                schema,
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(int),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ])
        )


@dataclass
class GroupID:
    default_gid: int | None = None

    @classmethod
    def uid_validator(
        cls,
        value: int | str | None,
    ) -> int:
        if value is None:
            assert cls.default_gid, "value is None but default_gid not provided"
        assert isinstance(value, (int, str)), "value must be an integer"
        match value:
            case int():
                if value == -1:
                    return os.getgid()
                else:
                    return value
            case str():
                try:
                    _value = int(value)
                    if _value == -1:
                        return os.getgid()
                    else:
                        return _value
                except ValueError:
                    try:
                        return pwd.getpwnam(value).pw_gid
                    except KeyError:
                        assert False, f"no such user {value} in system"

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = core_schema.chain_schema([
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ]),
            core_schema.no_info_plain_validator_function(cls.uid_validator),
        ])

        return core_schema.json_or_python_schema(
            json_schema=schema,
            python_schema=core_schema.union_schema([
                # check if it's an instance first before doing any further work
                core_schema.union_schema([
                    core_schema.is_instance_schema(int),
                    core_schema.is_instance_schema(str),
                ]),
                schema,
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(int),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ])
        )


class DebugConfig(BaseSchema):
    enabled: Annotated[bool, Field(default=False)]
    asyncio: Annotated[bool, Field(default=False)]
    enhanced_aiomonitor_task_info: Annotated[bool, Field(default=False)]
    log_events: Annotated[bool, Field(default=False)]
    log_stats: Annotated[bool, Field(default=False)]


class SecretConfig(BaseSchema):
    jwt_secret: Annotated[
        str,
        Field(
            description="String used for creating JWT signature. Must be identical across every nodes across single AppProxy cluster.",
            examples=["50M3V3RY53CR3T5TR1NG"],
        ),
    ]
    api_secret: Annotated[
        str,
        Field(
            description="API token used for validating requests from AppProxy worker and Backend.AI manager.",
            examples=["50M3TRULY53CR3T5TR1NG"],
        ),
    ]


class LogLevel(enum.StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    NOTSET = "NOTSET"


class LogFormat(enum.StrEnum):
    SIMPLE = "simple"
    VERBOSE = "verbose"


class LogDriver(enum.StrEnum):
    CONSOLE = "console"
    LOGSTASH = "logstash"
    FILE = "file"
    GRAYLOG = "graylog"


class LogstashProtocol(enum.StrEnum):
    ZMQ_PUSH = "zmq.push"
    ZMQ_PUB = "zmq.pub"
    TCP = "tcp"
    UDP = "udp"


default_pkg_ns = {"": "WARNING", "ai.backend": "DEBUG", "tests": "DEBUG", "aiohttp": "INFO"}


class ConsoleLogConfig(BaseSchema):
    colored: Annotated[
        bool | None, Field(default=None, description="Opt to print colorized log.", examples=[True])
    ]
    format: Annotated[
        LogFormat, Field(default=LogFormat.VERBOSE, description="Determine verbosity of log.")
    ]


class FileLogConfig(BaseSchema):
    path: Annotated[Path, Field(description="Path to store log.", examples=["/var/log/backend.ai"])]
    filename: Annotated[str, Field(description="Log file name.", examples=["coordinator.log"])]
    backup_count: Annotated[
        int, Field(description="Number of outdated log files to retain.", default=5)
    ]
    rotation_size: Annotated[
        ByteSize, Field(description="Maximum size for a single log file.", default="10M")
    ]
    format: Annotated[
        LogFormat, Field(default=LogFormat.VERBOSE, description="Determine verbosity of log.")
    ]


class LogstashConfig(BaseSchema):
    endpoint: Annotated[
        HostPortPair,
        Field(
            description="Connection information of logstash node.",
            examples=[HostPortPair(host="127.0.0.1", port=8001)],
        ),
    ]
    protocol: Annotated[
        LogstashProtocol,
        Field(
            description="Protocol to communicate with logstash server.",
            default=LogstashProtocol.TCP,
        ),
    ]
    ssl_enabled: Annotated[
        bool, Field(description="Use TLS to communicate with logstash server.", default=True)
    ]
    ssl_verify: Annotated[
        bool,
        Field(
            description="Verify validity of TLS certificate when communicating with logstash.",
            default=True,
        ),
    ]


class GraylogConfig(BaseSchema):
    host: Annotated[str, Field(description="Graylog hostname.", examples=["127.0.0.1"])]
    port: Annotated[int, Field(description="Graylog server port number.", examples=[8000])]
    level: Annotated[LogLevel, Field(description="Log level.", default=LogLevel.INFO)]
    ssl_verify: Annotated[
        bool,
        Field(
            description="Verify validity of TLS certificate when communicating with logstash.",
            default=True,
        ),
    ]
    ca_certs: Annotated[
        str | None,
        Field(
            description="Path to Root CA certificate file.",
            examples=["/etc/ssl/ca.pem"],
            default=None,
        ),
    ]
    keyfile: Annotated[
        str | None,
        Field(
            description="Path to TLS private key file.",
            examples=["/etc/backend.ai/graylog/privkey.pem"],
            default=None,
        ),
    ]
    certfile: Annotated[
        str | None,
        Field(
            description="Path to TLS certificate file.",
            examples=["/etc/backend.ai/graylog/cert.pem"],
            default=None,
        ),
    ]


class PyroscopeConfig(BaseSchema):
    application_name: str | None = Field(
        description="Pyroscope application name", default=None, examples=["proxy-worker-dev"]
    )
    server_address: str = Field(
        description="Pyroscope server endpoint", examples=["http://localhost:4040"]
    )
    sample_rate: int = Field(default=100, description="Pyroscope sample rate")
    detect_subprocesses: bool = Field(
        default=True,
        description="detect subprocesses started by the main process; default is False",
    )
    oncpu: bool = Field(default=True, description="report cpu time only; default is True")
    gil_only: bool = Field(
        default=True,
        description="only include traces for threads that are holding on to the Global Interpreter Lock; default is True",
    )
    enable_logging: bool = Field(
        default=True, description="does enable logging facility; default is False"
    )
    tags: dict[str, str] = Field(
        default={}, description="Pyroscope tags", examples=[{"environment": "dev"}]
    )


class ProfilingConfig(BaseSchema):
    enable_memray: bool = Field(default=False, description="Starts a memray live server.")
    memray_output_destination: Path = Field(
        default=Path("./memray-output.bin"),
        description="Path to store memray allocation captures.",
        examples=["/home/bai/proxy-worker/profiles/memray/proxy-worker.bin"],
    )
    enable_pyroscope: bool = Field(
        default=False, description="Allows sending pyroscope telemetry to pyroscope server."
    )
    pyroscope_config: PyroscopeConfig | None = Field(default=None)


class Undefined:
    pass


class UnsupportedTypeError(RuntimeError):
    pass


def generate_example_json(
    schema: type[BaseModel] | types.GenericAlias, parent: list[str] = []
) -> dict | list:
    if isinstance(schema, types.UnionType):
        return generate_example_json(typing.get_args(schema)[0], parent=[*parent])
    elif isinstance(schema, types.GenericAlias):
        if typing.get_origin(schema) is not list:
            raise RuntimeError("GenericAlias other than list not supported!")
        return [generate_example_json(typing.get_args(schema)[0], parent=[*parent])]
    elif issubclass(schema, BaseModel):
        res = {}
        for name, info in schema.model_fields.items():
            config_key = [*parent, name]
            assert info.annotation
            alternative_example = Undefined
            if info.examples:
                res[name] = info.examples[0]
            elif info.default != PydanticUndefined:
                alternative_example = info.default
            if name not in res:
                try:
                    res[name] = generate_example_json(info.annotation, parent=config_key)
                except RuntimeError:
                    if alternative_example != Undefined and alternative_example is not None:
                        res[name] = alternative_example
                    else:
                        raise
        return res
    else:
        raise UnsupportedTypeError(str(schema))


def get_default_redis_key_ttl() -> int:
    """
    Returns the default TTL for Redis keys.
    This is used to set the expiration time for keys in Redis.
    """
    return 2 * 24 * 60 * 60  # 2 days in seconds
