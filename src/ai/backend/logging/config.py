from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Self

from pydantic import (
    AliasChoices,
    BaseModel,
    ByteSize,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_serializer,
    model_validator,
)

from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
from ai.backend.common.typed_validators import AutoDirectoryPath

from .exceptions import ConfigurationError
from .types import LogFormat, LogLevel, MsgpackOptions
from .validation_context import BaseConfigValidationContext

default_pkg_ns = {
    "": LogLevel.WARNING,
    "ai.backend": LogLevel.INFO,
    "tests": LogLevel.DEBUG,
}


class LogDriver(StrEnum):
    CONSOLE = "console"
    LOGSTASH = "logstash"
    FILE = "file"
    GRAYLOG = "graylog"


class LogstashProtocol(StrEnum):
    ZMQ_PUSH = "zmq.push"
    ZMQ_PUB = "zmq.pub"
    TCP = "tcp"
    UDP = "udp"


class BaseConfigModel(BaseModel):
    @staticmethod
    def snake_to_kebab_case(string: str) -> str:
        if string == "class_":
            return "class"
        return string.replace("_", "-")

    model_config = ConfigDict(
        validate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
        extra="allow",
        alias_generator=snake_to_kebab_case,
    )


class HostPortPair(BaseConfigModel):
    host: str = Field(examples=["127.0.0.1"])
    port: int = Field(gt=0, lt=65536, examples=[8201])

    def __repr__(self) -> str:
        return f"{self.host}:{self.port}"

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, *args: Any) -> int | str:
        if args[0] == 0:
            return self.host
        if args[0] == 1:
            return self.port
        raise KeyError(*args)


class ConsoleConfig(BaseConfigModel):
    colored: Annotated[
        bool | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Opt to print colorized log.",
            added_version="24.09.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    format: Annotated[
        LogFormat,
        Field(default=LogFormat.VERBOSE),
        BackendAIConfigMeta(
            description="Determine verbosity of log.",
            added_version="24.09.0",
            example=ConfigExample(local="verbose", prod="verbose"),
        ),
    ]


class FileConfig(BaseConfigModel):
    path: Annotated[
        AutoDirectoryPath,
        Field(),
        BackendAIConfigMeta(
            description="Path to store log.",
            added_version="24.09.0",
            example=ConfigExample(local="/tmp/backend.ai/logs", prod="/var/log/backend.ai"),
        ),
    ]
    filename: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Log file name.",
            added_version="24.09.0",
            example=ConfigExample(local="manager.log", prod="manager.log"),
        ),
    ]
    backup_count: Annotated[
        int,
        Field(default=5),
        BackendAIConfigMeta(
            description="Number of outdated log files to retain.",
            added_version="24.09.0",
            example=ConfigExample(local="5", prod="10"),
        ),
    ]
    rotation_size: Annotated[
        ByteSize,
        Field(default_factory=lambda: ByteSize("10MB")),
        BackendAIConfigMeta(
            description="Maximum size for a single log file.",
            added_version="24.09.0",
            example=ConfigExample(local="10MB", prod="100MB"),
        ),
    ]
    format: Annotated[
        LogFormat,
        Field(default=LogFormat.VERBOSE),
        BackendAIConfigMeta(
            description="Determine verbosity of log.",
            added_version="24.09.0",
            example=ConfigExample(local="verbose", prod="verbose"),
        ),
    ]


class LogstashConfig(BaseConfigModel):
    endpoint: Annotated[
        HostPortPair,
        Field(),
        BackendAIConfigMeta(
            description="Connection information of logstash node.",
            added_version="24.09.0",
            example=ConfigExample(
                local='{ host = "127.0.0.1", port = 5044 }',
                prod='{ host = "logstash-server", port = 5044 }',
            ),
            composite=CompositeType.FIELD,
        ),
    ]
    protocol: Annotated[
        LogstashProtocol,
        Field(default=LogstashProtocol.TCP),
        BackendAIConfigMeta(
            description="Protocol to communicate with logstash server.",
            added_version="24.09.0",
            example=ConfigExample(local="tcp", prod="tcp"),
        ),
    ]
    ssl_enabled: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Use TLS to communicate with logstash server.",
            added_version="24.09.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    ssl_verify: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Verify validity of TLS certificate when communicating with logstash.",
            added_version="24.09.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]


class GraylogConfig(BaseConfigModel):
    host: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Graylog hostname.",
            added_version="24.09.0",
            example=ConfigExample(local="127.0.0.1", prod="graylog-server"),
        ),
    ]
    port: Annotated[
        int,
        Field(),
        BackendAIConfigMeta(
            description="Graylog server port number.",
            added_version="24.09.0",
            example=ConfigExample(local="12201", prod="12201"),
        ),
    ]
    level: Annotated[
        LogLevel,
        Field(default=LogLevel.INFO),
        BackendAIConfigMeta(
            description="Log level.",
            added_version="24.09.0",
            example=ConfigExample(local="DEBUG", prod="INFO"),
        ),
    ]
    localname: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="The custom source identifier. If not specified, fqdn will be used instead.",
            added_version="24.09.0",
            example=ConfigExample(local="dev-manager", prod="prod-manager-01"),
        ),
    ]
    fqdn: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="The fully qualified domain name of the source.",
            added_version="24.09.0",
            example=ConfigExample(local="localhost", prod="manager.backend.ai"),
        ),
    ]
    ssl_verify: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description="Verify validity of TLS certificate when communicating with Graylog.",
            added_version="24.09.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    ca_certs: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Path to Root CA certificate file.",
            added_version="24.09.0",
            example=ConfigExample(local="/etc/ssl/ca.pem", prod="/etc/ssl/ca.pem"),
        ),
    ]
    keyfile: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Path to TLS private key file.",
            added_version="24.09.0",
            example=ConfigExample(
                local="/etc/backend.ai/graylog/privkey.pem",
                prod="/etc/backend.ai/graylog/privkey.pem",
            ),
            secret=True,
        ),
    ]
    certfile: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Path to TLS certificate file.",
            added_version="24.09.0",
            example=ConfigExample(
                local="/etc/backend.ai/graylog/cert.pem",
                prod="/etc/backend.ai/graylog/cert.pem",
            ),
        ),
    ]


class LogHandlerConfig(BaseConfigModel):
    class_: str = Field(
        alias="class",
        description="The class name of the log handler.",
    )
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="The log level to filter messages from this handler.",
    )

    @model_serializer(mode="wrap")
    def rename_class(
        self,
        handler: Any,
    ) -> dict[str, Any]:
        data = handler(self)
        if "class_" in data:
            data["class"] = data.pop("class_")
        return data


class RelayLogHandlerConfig(LogHandlerConfig):
    class_: str = Field(
        alias="class",
        description="The class name of the log handler.",
    )
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="The log level to filter messages from this handler.",
    )
    endpoint: str
    msgpack_options: MsgpackOptions


class LoggerConfig(BaseConfigModel):
    handlers: list[str] = Field(
        default_factory=list,
        description="The name of handlers receiving messages from this logger.",
    )
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="The log level to filter messages from this logger.",
    )
    propagate: bool = Field(
        default=True,
        description="Whether to propagate messages to pre-existing loggers.",
    )


class LoggingConfig(BaseConfigModel):
    # Fields to be dumped for Python's standard logging
    version: Annotated[
        int,
        Field(default=1),
        BackendAIConfigMeta(
            description="The version used by logging.dictConfig().",
            added_version="24.09.0",
            example=ConfigExample(local="1", prod="1"),
        ),
    ]
    level: Annotated[
        LogLevel,
        Field(default=LogLevel.INFO),
        BackendAIConfigMeta(
            description="The main log level to filter messages from all loggers.",
            added_version="24.09.0",
            example=ConfigExample(local="DEBUG", prod="INFO"),
        ),
    ]
    disable_existing_loggers: Annotated[
        bool,
        Field(default=False, serialization_alias="disable-existing-loggers"),
        BackendAIConfigMeta(
            description="Disable the existing loggers when applying the config.",
            added_version="24.09.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    handlers: Annotated[
        dict[str, LogHandlerConfig | RelayLogHandlerConfig],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description="The mapping of log handler configurations.",
            added_version="24.09.0",
            example=ConfigExample(local="{ }", prod="{ }"),
        ),
    ]
    loggers: Annotated[
        dict[str, LoggerConfig],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description="The mapping of per-namespace logger configurations.",
            added_version="24.09.0",
            example=ConfigExample(local="{ }", prod="{ }"),
        ),
    ]

    # Backend.AI-specific configs from here
    drivers: Annotated[
        list[LogDriver],
        Field(default=[LogDriver.CONSOLE]),
        BackendAIConfigMeta(
            description="The list of log drivers to activate.",
            added_version="24.09.0",
            example=ConfigExample(local='["console"]', prod='["console", "file"]'),
        ),
    ]

    # Per-driver configs
    console: Annotated[
        ConsoleConfig,
        Field(default=ConsoleConfig(colored=None, format=LogFormat.VERBOSE)),
        BackendAIConfigMeta(
            description="Console logging driver configuration.",
            added_version="24.09.0",
            composite=CompositeType.FIELD,
        ),
    ]
    file: Annotated[
        FileConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="File logging driver configuration.",
            added_version="24.09.0",
            composite=CompositeType.FIELD,
        ),
    ]
    logstash: Annotated[
        LogstashConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Logstash logging driver configuration.",
            added_version="24.09.0",
            composite=CompositeType.FIELD,
        ),
    ]
    graylog: Annotated[
        GraylogConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Graylog logging driver configuration.",
            added_version="24.09.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # Per-pkg log levels
    pkg_ns: Annotated[
        dict[str, LogLevel],
        Field(
            default=default_pkg_ns,
            validation_alias=AliasChoices("pkg_ns", "pkg-ns"),
            serialization_alias="pkg-ns",
        ),
        BackendAIConfigMeta(
            description="Override default log level for specific scope of package.",
            added_version="24.09.0",
            example=ConfigExample(
                local='{ "" = "WARNING", "ai.backend" = "DEBUG" }',
                prod='{ "" = "WARNING", "ai.backend" = "INFO" }',
            ),
        ),
    ]

    @field_validator("level", mode="before")
    @classmethod
    def _set_level(cls, v: Any, info: ValidationInfo) -> Any:
        context = BaseConfigValidationContext.get_config_validation_context(info)
        if context is None:
            # In tests or server scripts that do not use Pydantic validation yet.
            # Command line args are not set.
            return v

        if context.log_level != LogLevel.NOTSET:
            return context.log_level
        return v

    @field_validator("pkg_ns", mode="before")
    @classmethod
    def _set_pkg_ns(cls, v: Any, info: ValidationInfo) -> Any:
        context = BaseConfigValidationContext.get_config_validation_context(info)
        if context is None:
            # In tests or server scripts that do not use Pydantic validation yet.
            # Command line args are not set.
            return v

        if context.log_level != LogLevel.NOTSET:
            v = {} if v is None else dict(v)
            v["ai.backend"] = context.log_level
        return v

    @model_validator(mode="after")
    def validate_driver_configs(self) -> Self:
        for driver in self.drivers:
            if getattr(self, driver, None) is None:
                raise ConfigurationError({
                    "logging": f"{driver} driver is activated but no config given."
                })
        return self
