from enum import StrEnum
from typing import Optional, Self

from pydantic import (
    AliasChoices,
    BaseModel,
    ByteSize,
    ConfigDict,
    Field,
    model_serializer,
    model_validator,
)

from ai.backend.common.typed_validators import AutoDirectoryPath

from .exceptions import ConfigurationError
from .types import LogFormat, LogLevel, MsgpackOptions

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

    def __getitem__(self, *args) -> int | str:
        if args[0] == 0:
            return self.host
        elif args[0] == 1:
            return self.port
        else:
            raise KeyError(*args)


class ConsoleConfig(BaseConfigModel):
    colored: Optional[bool] = Field(
        default=None, description="Opt to print colorized log.", examples=[True]
    )
    format: LogFormat = Field(default=LogFormat.VERBOSE, description="Determine verbosity of log.")


class FileConfig(BaseConfigModel):
    path: AutoDirectoryPath = Field(
        description="Path to store log.", examples=["/var/log/backend.ai"]
    )
    filename: str = Field(description="Log file name.", examples=["wsproxy.log"])
    backup_count: int = Field(description="Number of outdated log files to retain.", default=5)
    rotation_size: ByteSize = Field(
        description="Maximum size for a single log file.",
        default_factory=lambda: ByteSize("10MB"),
    )
    format: LogFormat = Field(default=LogFormat.VERBOSE, description="Determine verbosity of log.")


class LogstashConfig(BaseConfigModel):
    endpoint: HostPortPair = Field(
        description="Connection information of logstash node.",
        examples=[HostPortPair(host="127.0.0.1", port=8001)],
    )
    protocol: LogstashProtocol = Field(
        description="Protocol to communicate with logstash server.",
        default=LogstashProtocol.TCP,
    )
    ssl_enabled: bool = Field(
        description="Use TLS to communicate with logstash server.",
        default=True,
    )
    ssl_verify: bool = Field(
        description="Verify validity of TLS certificate when communicating with logstash.",
        default=True,
    )


class GraylogConfig(BaseConfigModel):
    host: str = Field(description="Graylog hostname.", examples=["127.0.0.1"])
    port: int = Field(description="Graylog server port number.", examples=[8000])
    level: LogLevel = Field(description="Log level.", default=LogLevel.INFO)
    localname: Optional[str] = Field(
        default=None,
        description="The custom source identifier. If not specified, fqdn will be used instead.",
    )
    fqdn: Optional[str] = Field(
        default=None,
        description="The fuly qualified domain name of the source.",
    )
    ssl_verify: bool = Field(
        description="Verify validity of TLS certificate when communicating with logstash.",
        default=True,
    )
    ca_certs: Optional[str] = Field(
        description="Path to Root CA certificate file.",
        examples=["/etc/ssl/ca.pem"],
        default=None,
    )
    keyfile: Optional[str] = Field(
        description="Path to TLS private key file.",
        examples=["/etc/backend.ai/graylog/privkey.pem"],
        default=None,
    )
    certfile: Optional[str] = Field(
        description="Path to TLS certificate file.",
        examples=["/etc/backend.ai/graylog/cert.pem"],
        default=None,
    )


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
    def rename_class(self, handler):
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
    version: int = Field(default=1, description="The version used by logging.dictConfig().")
    level: LogLevel = Field(
        default=LogLevel.INFO, description="The main log level to filter messages from all loggers."
    )
    disable_existing_loggers: bool = Field(
        default=False,
        description="Disable the existing loggers when applying the config.",
    )
    handlers: dict[str, LogHandlerConfig | RelayLogHandlerConfig] = Field(
        default_factory=dict, description="The mapping of log handler configurations."
    )
    loggers: dict[str, LoggerConfig] = Field(
        default_factory=dict, description="The mapping of per-namespace logger configurations."
    )

    # Backend.AI-specific configs from here
    drivers: list[LogDriver] = Field(
        default=[LogDriver.CONSOLE], description="The list of log drivers to activate."
    )

    # Per-driver configs
    console: ConsoleConfig = Field(default=ConsoleConfig(colored=None, format=LogFormat.VERBOSE))
    file: Optional[FileConfig] = Field(default=None)
    logstash: Optional[LogstashConfig] = Field(default=None)
    graylog: Optional[GraylogConfig] = Field(default=None)

    # Per-pkg log levels
    pkg_ns: dict[str, LogLevel] = Field(
        description="Override default log level for specific scope of package",
        default=default_pkg_ns,
        validation_alias=AliasChoices("pkg_ns", "pkg-ns"),
        serialization_alias="pkg-ns",
    )

    @model_validator(mode="after")
    def validate_driver_configs(self) -> Self:
        for driver in self.drivers:
            if getattr(self, driver, None) is None:
                raise ConfigurationError({
                    "logging": f"{driver} driver is activated but no config given."
                })
        return self
