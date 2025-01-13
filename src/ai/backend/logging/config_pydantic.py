import enum
from pathlib import Path
from typing import Annotated

from pydantic import ByteSize, Field

from ai.backend.common.config import BaseSchema

from .types import LogFormat, LogLevel

default_pkg_ns = {
    "": LogLevel.WARNING,
    "ai.backend": LogLevel.DEBUG,
    "tests": LogLevel.DEBUG,
    "aiohttp": LogLevel.INFO,
}


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


class ConsoleConfig(BaseSchema):
    colored: bool | None = Field(
        default=None, description="Opt to print colorized log.", examples=[True]
    )
    format: LogFormat = Field(default=LogFormat.VERBOSE, description="Determine verbosity of log.")


class FileConfig(BaseSchema):
    path: Path = Field(description="Path to store log.", examples=["/var/log/backend.ai"])
    filename: str = Field(description="Log file name.", examples=["wsproxy.log"])
    backup_count: int = Field(
        description="Number of outdated log files to retain.", default=5, alias="backup-count"
    )
    rotation_size: ByteSize = Field(
        description="Maximum size for a single log file.",
        default_factory=lambda: ByteSize("10MB"),
    )
    format: LogFormat = Field(default=LogFormat.VERBOSE, description="Determine verbosity of log.")


class LogstashConfig(BaseSchema):
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
        alias="ssl-enabled",
    )
    ssl_verify: bool = Field(
        description="Verify validity of TLS certificate when communicating with logstash.",
        default=True,
        alias="ssl-verify",
    )


class GraylogConfig(BaseSchema):
    host: str = Field(description="Graylog hostname.", examples=["127.0.0.1"])
    port: int = Field(description="Graylog server port number.", examples=[8000])
    level: LogLevel = Field(description="Log level.", default=LogLevel.INFO)
    ssl_verify: bool = Field(
        description="Verify validity of TLS certificate when communicating with logstash.",
        default=True,
        alias="ssl-verify",
    )
    ca_certs: str | None = Field(
        description="Path to Root CA certificate file.",
        examples=["/etc/ssl/ca.pem"],
        default=None,
        alias="ca-certs",
    )
    keyfile: str | None = Field(
        description="Path to TLS private key file.",
        examples=["/etc/backend.ai/graylog/privkey.pem"],
        default=None,
    )
    certfile: str | None = Field(
        description="Path to TLS certificate file.",
        examples=["/etc/backend.ai/graylog/cert.pem"],
        default=None,
    )


class LoggingConfig(BaseSchema):
    level: LogLevel = Field(default=LogLevel.INFO, description="Log level.")
    drivers: list[LogDriver] = Field(
        default=[LogDriver.CONSOLE], description="Array of log drivers to print."
    )
    console: ConsoleConfig = Field(default=ConsoleConfig(colored=None, format=LogFormat.VERBOSE))
    file: FileConfig | None = Field(default=None)
    logstash: LogstashConfig | None = Field(default=None)
    graylog: GraylogConfig | None = Field(default=None)
    pkg_ns: dict[str, LogLevel] = Field(
        description="Override default log level for specific scope of package",
        default=default_pkg_ns,
        alias="pkg-ns",
    )
