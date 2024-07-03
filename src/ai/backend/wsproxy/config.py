import enum
import os
import pwd
import socket
import sys
import types
import typing
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat
from typing import Annotated, Any

import click
from pydantic import (
    BaseModel,
    ByteSize,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticUndefined, core_schema

from ai.backend.common import config

from .types import EventLoopType, ProxyProtocol

_file_perm = (Path(__file__).parent / "server.py").stat()


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


class HostPortPair(BaseSchema):
    host: Annotated[str, Field(examples=["127.0.0.1"])]
    port: Annotated[int, Field(gt=0, lt=65536, examples=[8201])]

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


class LogLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    NOTSET = "NOTSET"


class LogFormat(str, enum.Enum):
    SIMPLE = "simple"
    VERBOSE = "verbose"


class LogDriver(str, enum.Enum):
    CONSOLE = "console"
    LOGSTASH = "logstash"
    FILE = "file"
    GRAYLOG = "graylog"


class LogstashProtocol(str, enum.Enum):
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
    filename: Annotated[str, Field(description="Log file name.", examples=["wsproxy.log"])]
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


class LoggingConfig(BaseSchema):
    level: Annotated[LogLevel, Field(default=LogLevel.INFO, description="Log level.")]
    pkg_ns: Annotated[
        dict[str, LogLevel],
        Field(
            description="Override default log level for specific scope of package",
            default=default_pkg_ns,
        ),
    ]
    drivers: Annotated[
        list[LogDriver],
        Field(default=[LogDriver.CONSOLE], description="Array of log drivers to print."),
    ]
    console: Annotated[
        ConsoleLogConfig, Field(default=ConsoleLogConfig(colored=None, format=LogFormat.VERBOSE))
    ]
    file: Annotated[FileLogConfig | None, Field(default=None)]
    logstash: Annotated[LogstashConfig | None, Field(default=None)]
    graylog: Annotated[GraylogConfig | None, Field(default=None)]


class DebugConfig(BaseSchema):
    enabled: Annotated[bool, Field(default=False)]
    asyncio: Annotated[bool, Field(default=False)]
    enhanced_aiomonitor_task_info: Annotated[bool, Field(default=False)]
    log_events: Annotated[bool, Field(default=False)]


class WSProxyConfig(BaseSchema):
    ipc_base_path: Annotated[
        Path,
        Field(
            default=Path("/tmp/backend.ai/ipc"),
            description="Directory to store temporary UNIX sockets.",
        ),
    ]
    event_loop: Annotated[
        EventLoopType,
        Field(default=EventLoopType.ASYNCIO, description="Type of event loop to use."),
    ]
    pid_file: Annotated[
        Path,
        Field(
            default=Path(os.devnull),
            description="Place to store process PID.",
            examples=["/run/backend.ai/wsproxy/wsproxy.pid"],
        ),
    ]

    id: Annotated[
        str,
        Field(default=f"i-{socket.gethostname()}", examples=["i-node01"], description="Node id."),
    ]
    user: Annotated[
        int,
        UserID(default_uid=_file_perm.st_uid),
        Field(default=_file_perm.st_uid, description="Process owner."),
    ]
    group: Annotated[
        int,
        GroupID(default_gid=_file_perm.st_gid),
        Field(default=_file_perm.st_uid, description="Process group."),
    ]

    bind_host: Annotated[
        str,
        Field(
            default="0.0.0.0",
            description="Bind address of the port opened on behalf of wsproxy worker",
        ),
    ]
    advertised_host: Annotated[
        str, Field(examples=["example.com"], description="Hostname to be advertised to client")
    ]

    bind_api_port: Annotated[
        int, Field(default=5050, description="Port number to bind for API server")
    ]
    advertised_api_port: Annotated[
        int | None,
        Field(default=None, examples=[15050], description="API port number reachable from client"),
    ]

    bind_proxy_port_range: Annotated[
        tuple[int, int],
        Field(default=[10200, 10300], description="Port number to bind for actual traffic"),
    ]
    advertised_proxy_port_range: Annotated[
        tuple[int, int] | None,
        Field(
            default=None,
            examples=[[20200, 20300]],
            description="Traffic port range reachable from client",
        ),
    ]

    protocol: Annotated[
        ProxyProtocol, Field(default=ProxyProtocol.HTTP, description="Proxy protocol")
    ]

    jwt_encrypt_key: Annotated[
        str, Field(examples=["50M3G00DL00KING53CR3T"], description="JWT encryption key")
    ]
    permit_hash_key: Annotated[
        str, Field(examples=["50M3G00DL00KING53CR3T"], description="Permit hash key")
    ]

    api_secret: Annotated[str, Field(examples=["50M3G00DL00KING53CR3T"], description="API secret")]

    aiomonitor_termui_port: Annotated[
        int,
        Field(
            gt=0, lt=65536, description="Port number for aiomonitor termui server.", default=48500
        ),
    ]
    aiomonitor_webui_port: Annotated[
        int,
        Field(
            gt=0, lt=65536, description="Port number for aiomonitor webui server.", default=49500
        ),
    ]


class ServerConfig(BaseSchema):
    wsproxy: WSProxyConfig
    logging: LoggingConfig
    debug: DebugConfig


def load(config_path: Path | None = None, log_level: str = "INFO") -> ServerConfig:
    # Determine where to read configuration.
    raw_cfg, _ = config.read_from_file(config_path, "wsproxy")

    config.override_key(raw_cfg, ("debug", "enabled"), log_level == "DEBUG")
    config.override_key(raw_cfg, ("logging", "level"), log_level.upper())
    config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level.upper())
    config.override_key(raw_cfg, ("logging", "pkg-ns", "aiohttp"), log_level.upper())

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-copmatible)
    try:
        cfg = ServerConfig(**raw_cfg)
        if cfg.debug.enabled:
            print("== WSProxy configuration ==", file=sys.stderr)
            print(pformat(cfg.model_dump()), file=sys.stderr)
    except ValidationError as e:
        print(
            "ConfigurationError: Could not read or validate the manager local config:",
            file=sys.stderr,
        )
        print(pformat(e), file=sys.stderr)
        raise click.Abort()
    else:
        return cfg


class Undefined:
    pass


class UnsupportedTypeError(RuntimeError):
    pass


def generate_example_json(
    schema: type[BaseSchema] | types.GenericAlias | types.UnionType, parent: list[str] = []
) -> dict | list:
    if isinstance(schema, types.UnionType):
        return generate_example_json(typing.get_args(schema)[0], parent=[*parent])
    elif isinstance(schema, types.GenericAlias):
        if typing.get_origin(schema) != list:
            raise RuntimeError("GenericAlias other than list not supported!")
        return [generate_example_json(typing.get_args(schema)[0], parent=[*parent])]
    elif issubclass(schema, BaseSchema):
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
                    if alternative_example != Undefined:
                        res[name] = alternative_example
                    else:
                        raise
        return res
    else:
        raise UnsupportedTypeError(str(schema))
