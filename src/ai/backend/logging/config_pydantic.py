import enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ByteSize, ConfigDict, Field

from .types import LogFormat, LogLevel

default_pkg_ns = {"": "WARNING", "ai.backend": "DEBUG", "tests": "DEBUG", "aiohttp": "INFO"}


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


class ConsoleConfig(BaseSchema):
    colored: Annotated[
        bool | None, Field(default=None, description="Opt to print colorized log.", examples=[True])
    ]
    format: Annotated[
        LogFormat, Field(default=LogFormat.VERBOSE, description="Determine verbosity of log.")
    ]


class FileConfig(BaseSchema):
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
    drivers: Annotated[
        list[LogDriver],
        Field(default=[LogDriver.CONSOLE], description="Array of log drivers to print."),
    ]
    console: Annotated[
        ConsoleConfig, Field(default=ConsoleConfig(colored=None, format=LogFormat.VERBOSE))
    ]
    file: Annotated[FileConfig | None, Field(default=None)]
    logstash: Annotated[LogstashConfig | None, Field(default=None)]
    graylog: Annotated[GraylogConfig | None, Field(default=None)]
    pkg_ns: Annotated[
        dict[str, LogLevel],
        Field(
            description="Override default log level for specific scope of package",
            default=default_pkg_ns,
        ),
    ]
