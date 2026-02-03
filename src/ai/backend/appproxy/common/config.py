import enum
import pwd
import types
import typing
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

from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample

from .errors import (
    GroupNotFoundError,
    InvalidGIDTypeError,
    InvalidUIDTypeError,
    MissingAnnotationError,
    UserNotFoundError,
)
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
        Field(),
        BackendAIConfigMeta(
            description="Secret string used for creating permit hash.",
            added_version="25.13.0",
            secret=True,
            example=ConfigExample(local="PERMIT_HASH_SECRET", prod="PERMIT_HASH_SECRET"),
        ),
    ]
    digest_mod: Annotated[
        DigestModType,
        Field(default=DigestModType.SHA256),
        BackendAIConfigMeta(
            description="Hash digest method to use.",
            added_version="25.13.0",
            example=ConfigExample(local="SHA256", prod="SHA256"),
        ),
    ]


class HostPortPair(BaseSchema):
    host: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Hostname or IP address.",
            added_version="25.13.0",
            example=ConfigExample(local="127.0.0.1", prod="server.example.com"),
        ),
    ]
    port: Annotated[
        int,
        Field(gt=0, lt=65536),
        BackendAIConfigMeta(
            description="Port number.",
            added_version="25.13.0",
            example=ConfigExample(local="8201", prod="8201"),
        ),
    ]

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

    def __getitem__(self, *args: object) -> int | str:
        if args[0] == 0:
            return self.host
        if args[0] == 1:
            return self.port
        raise KeyError(*args)


class RedisHelperConfig(BaseSchema):
    socket_timeout: Annotated[
        float,
        Field(default=5.0),
        BackendAIConfigMeta(
            description="Timeout in seconds for Redis socket operations.",
            added_version="25.13.0",
            example=ConfigExample(local="5.0", prod="10.0"),
        ),
    ]
    socket_connect_timeout: Annotated[
        float,
        Field(default=2.0),
        BackendAIConfigMeta(
            description="Timeout in seconds for establishing Redis connections.",
            added_version="25.13.0",
            example=ConfigExample(local="2.0", prod="5.0"),
        ),
    ]
    reconnect_poll_timeout: Annotated[
        float,
        Field(default=0.3),
        BackendAIConfigMeta(
            description="Time in seconds to wait between reconnection attempts.",
            added_version="25.13.0",
            example=ConfigExample(local="0.3", prod="1.0"),
        ),
    ]


class RedisConfig(BaseSchema):
    addr: Annotated[
        HostPortPair | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Address and port number of redis server.",
            added_version="25.13.0",
            example=ConfigExample(local="127.0.0.1:6379", prod="redis-server:6379"),
        ),
    ]
    sentinel: Annotated[
        list[HostPortPair] | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="List of address/port pair of sentinel servers.",
            added_version="25.13.0",
            example=ConfigExample(
                local="",
                prod="redis-sentinel:26379,redis-sentinel:26380",
            ),
        ),
    ]
    service_name: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Redis service name.",
            added_version="25.13.0",
            example=ConfigExample(local="mymaster", prod="bai-service"),
        ),
    ]
    password: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Redis password.",
            added_version="25.13.0",
            secret=True,
            example=ConfigExample(local="", prod="REDIS_PASSWORD"),
        ),
    ]
    redis_helper_config: Annotated[
        RedisHelperConfig,
        Field(default_factory=lambda: RedisHelperConfig()),
        BackendAIConfigMeta(
            description="Configuration for Redis helper library.",
            added_version="25.13.0",
            composite=CompositeType.FIELD,
        ),
    ]

    def to_dict(self) -> dict[str, Any]:
        base = self.model_dump()
        if self.addr:
            base["addr"] = f"{self.addr.host}:{self.addr.port}"
        if self.sentinel:
            base["sentinel"] = ",".join([f"{r.host}:{r.port}" for r in self.sentinel])
        return base


class UserIDValidator:
    @classmethod
    def uid_validator(
        cls,
        value: int | str,
    ) -> int:
        if not isinstance(value, (int, str)):
            raise InvalidUIDTypeError("UID must be an integer or string")
        match value:
            case int():
                return value
            case str():
                try:
                    return int(value)
                except ValueError:
                    try:
                        return pwd.getpwnam(value).pw_uid
                    except KeyError as e:
                        raise UserNotFoundError(f"No such user {value} in system") from e

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
        cls, _: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ])
        )


class GroupIDValidator:
    @classmethod
    def uid_validator(
        cls,
        value: int | str,
    ) -> int:
        if not isinstance(value, (int, str)):
            raise InvalidGIDTypeError("GID must be an integer or string")
        match value:
            case int():
                return value
            case str():
                try:
                    return int(value)
                except ValueError:
                    try:
                        return pwd.getpwnam(value).pw_gid
                    except KeyError as e:
                        raise GroupNotFoundError(f"No such group {value} in system") from e

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
        cls, _: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ])
        )


class DebugConfig(BaseSchema):
    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description="Enable debug mode.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    asyncio: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description="Enable asyncio debug mode.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    enhanced_aiomonitor_task_info: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description="Enable enhanced aiomonitor task info.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    log_events: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description="Enable event logging.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    log_stats: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description="Enable statistics logging.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]


class SecretConfig(BaseSchema):
    jwt_secret: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "String used for creating JWT signature. "
                "Must be identical across every nodes across single AppProxy cluster."
            ),
            added_version="25.13.0",
            secret=True,
            example=ConfigExample(local="JWT_SECRET", prod="JWT_SECRET"),
        ),
    ]
    api_secret: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "API token used for validating requests from AppProxy worker "
                "and Backend.AI manager."
            ),
            added_version="25.13.0",
            secret=True,
            example=ConfigExample(local="API_SECRET", prod="API_SECRET"),
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
        bool | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Opt to print colorized log.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    format: Annotated[
        LogFormat,
        Field(default=LogFormat.VERBOSE),
        BackendAIConfigMeta(
            description="Determine verbosity of log.",
            added_version="25.13.0",
            example=ConfigExample(local="verbose", prod="simple"),
        ),
    ]


class FileLogConfig(BaseSchema):
    path: Annotated[
        Path,
        Field(),
        BackendAIConfigMeta(
            description="Path to store log.",
            added_version="25.13.0",
            example=ConfigExample(local="./logs", prod="/var/log/backend.ai"),
        ),
    ]
    filename: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Log file name.",
            added_version="25.13.0",
            example=ConfigExample(local="coordinator.log", prod="coordinator.log"),
        ),
    ]
    backup_count: Annotated[
        int,
        Field(default=5),
        BackendAIConfigMeta(
            description="Number of outdated log files to retain.",
            added_version="25.13.0",
            example=ConfigExample(local="5", prod="10"),
        ),
    ]
    rotation_size: Annotated[
        ByteSize,
        Field(default="10M"),
        BackendAIConfigMeta(
            description="Maximum size for a single log file.",
            added_version="25.13.0",
            example=ConfigExample(local="10M", prod="100M"),
        ),
    ]
    format: Annotated[
        LogFormat,
        Field(default=LogFormat.VERBOSE),
        BackendAIConfigMeta(
            description="Determine verbosity of log.",
            added_version="25.13.0",
            example=ConfigExample(local="verbose", prod="simple"),
        ),
    ]


class LogstashConfig(BaseSchema):
    endpoint: Annotated[
        HostPortPair,
        Field(),
        BackendAIConfigMeta(
            description="Connection information of logstash node.",
            added_version="25.13.0",
            example=ConfigExample(local="127.0.0.1:5000", prod="logstash:5000"),
        ),
    ]
    protocol: Annotated[
        LogstashProtocol,
        Field(default=LogstashProtocol.TCP),
        BackendAIConfigMeta(
            description="Protocol to communicate with logstash server.",
            added_version="25.13.0",
            example=ConfigExample(local="tcp", prod="tcp"),
        ),
    ]
    ssl_enabled: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Use TLS to communicate with logstash server.",
            added_version="25.13.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    ssl_verify: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Verify validity of TLS certificate when communicating with logstash.",
            added_version="25.13.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]


class GraylogConfig(BaseSchema):
    host: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Graylog hostname.",
            added_version="25.13.0",
            example=ConfigExample(local="127.0.0.1", prod="graylog.example.com"),
        ),
    ]
    port: Annotated[
        int,
        Field(),
        BackendAIConfigMeta(
            description="Graylog server port number.",
            added_version="25.13.0",
            example=ConfigExample(local="12201", prod="12201"),
        ),
    ]
    level: Annotated[
        LogLevel,
        Field(default=LogLevel.INFO),
        BackendAIConfigMeta(
            description="Log level.",
            added_version="25.13.0",
            example=ConfigExample(local="DEBUG", prod="INFO"),
        ),
    ]
    ssl_verify: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Verify validity of TLS certificate when communicating with graylog.",
            added_version="25.13.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    ca_certs: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Path to Root CA certificate file.",
            added_version="25.13.0",
            example=ConfigExample(local="", prod="/etc/ssl/ca.pem"),
        ),
    ]
    keyfile: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Path to TLS private key file.",
            added_version="25.13.0",
            example=ConfigExample(local="", prod="/etc/backend.ai/graylog/privkey.pem"),
            secret=True,
        ),
    ]
    certfile: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Path to TLS certificate file.",
            added_version="25.13.0",
            example=ConfigExample(local="", prod="/etc/backend.ai/graylog/cert.pem"),
        ),
    ]


class PyroscopeConfig(BaseSchema):
    application_name: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Pyroscope application name.",
            added_version="25.13.0",
            example=ConfigExample(local="proxy-worker-dev", prod="proxy-worker-prod"),
        ),
    ]
    server_address: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Pyroscope server endpoint.",
            added_version="25.13.0",
            example=ConfigExample(local="http://localhost:4040", prod="http://pyroscope:4040"),
        ),
    ]
    sample_rate: Annotated[
        int,
        Field(default=100),
        BackendAIConfigMeta(
            description="Pyroscope sample rate.",
            added_version="25.13.0",
            example=ConfigExample(local="100", prod="100"),
        ),
    ]
    detect_subprocesses: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Detect subprocesses started by the main process.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    oncpu: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Report cpu time only.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    gil_only: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description=(
                "Only include traces for threads that are holding on to "
                "the Global Interpreter Lock."
            ),
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    enable_logging: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Enable logging facility.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    tags: Annotated[
        dict[str, str],
        Field(default={}),
        BackendAIConfigMeta(
            description="Pyroscope tags.",
            added_version="25.13.0",
            composite=CompositeType.FIELD,
        ),
    ]


class ProfilingConfig(BaseSchema):
    enable_memray: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description="Starts a memray live server.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    memray_output_destination: Annotated[
        Path,
        Field(default=Path("./memray-output.bin")),
        BackendAIConfigMeta(
            description="Path to store memray allocation captures.",
            added_version="25.13.0",
            example=ConfigExample(
                local="./memray-output.bin",
                prod="/var/log/backend.ai/memray/proxy-worker.bin",
            ),
        ),
    ]
    enable_pyroscope: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description="Allows sending pyroscope telemetry to pyroscope server.",
            added_version="25.13.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    pyroscope_config: Annotated[
        PyroscopeConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Pyroscope configuration.",
            added_version="25.13.0",
            composite=CompositeType.FIELD,
        ),
    ]


class Undefined:
    pass


class UnsupportedTypeError(RuntimeError):
    pass


def generate_example_json(
    schema: type[BaseModel] | types.GenericAlias | types.UnionType,
    parent: list[str] | None = None,
) -> dict[str, Any] | list[Any]:
    if parent is None:
        parent = []
    if isinstance(schema, types.UnionType):
        return generate_example_json(typing.get_args(schema)[0], parent=[*parent])
    if isinstance(schema, types.GenericAlias):
        if typing.get_origin(schema) is not list:
            raise RuntimeError("GenericAlias other than list not supported!")
        return [generate_example_json(typing.get_args(schema)[0], parent=[*parent])]
    if issubclass(schema, BaseModel):
        res = {}
        for name, info in schema.model_fields.items():
            config_key = [*parent, name]
            if not info.annotation:
                raise MissingAnnotationError(f"Field '{name}' is missing type annotation")
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
    raise UnsupportedTypeError(str(schema))


def get_default_redis_key_ttl() -> int:
    """
    Returns the default TTL for Redis keys.
    This is used to set the expiration time for keys in Redis.
    """
    return 2 * 24 * 60 * 60  # 2 days in seconds
