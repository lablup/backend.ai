import enum
import os
import socket
import sys
from pathlib import Path
from pprint import pformat
from typing import Annotated

import click
from pydantic import Field, FilePath, ValidationError

from ai.backend.appproxy.common.config import (
    BaseSchema,
    DebugConfig,
    GroupID,
    HostPortPair,
    PermitHashConfig,
    ProfilingConfig,
    RedisConfig,
    SecretConfig,
    UserID,
)
from ai.backend.appproxy.common.exceptions import ConfigValidationError
from ai.backend.appproxy.common.types import EventLoopType
from ai.backend.common import config
from ai.backend.common.types import ServiceDiscoveryType
from ai.backend.logging import LogLevel
from ai.backend.logging.config import LoggingConfig

_file_perm = (Path(__file__).parent / "server.py").stat()


class DBType(enum.StrEnum):
    POSTGRESQL = "postgresql"


class DistributedLock(enum.StrEnum):
    FILELOCK = "filelock"
    PG_ADVISORY = "pg_advisory"
    REDLOCK = "redlock"


class RedisLockConfig(BaseSchema):
    lock_retry_interval: Annotated[float | None, Field(default=None)]


class DBConfig(BaseSchema):
    type: Annotated[DBType, Field(description="Database type.", examples=[DBType.POSTGRESQL])]
    addr: Annotated[
        HostPortPair,
        Field(
            description="Address and port number of database server.",
            examples=[HostPortPair(host="127.0.0.1", port=8201)],
        ),
    ]
    name: Annotated[
        str, Field(min_length=2, max_length=64, description="Database name.", examples=["appproxy"])
    ]
    user: Annotated[str, Field(description="Database username.", examples=["backend"])]
    password: Annotated[str, Field(description="Databsase password.", examples=["develove"])]
    pool_size: Annotated[int, Field(gt=0, default=8)]
    max_overflow: Annotated[int, Field(gt=-2, default=64)]


class EtcdConfig(BaseSchema):
    addr: HostPortPair
    password: Annotated[str | None, Field(default=None)]
    namespace: Annotated[str, Field(default="traefik")]


class TraefikConfig(BaseSchema):
    etcd: EtcdConfig


class OTELConfig(BaseSchema):
    enabled: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "Whether to enable OpenTelemetry for tracing or logging. "
                "When enabled, traces or log will be collected and sent to the configured OTLP endpoint."
            ),
            examples=[True, False],
        ),
    ]
    log_level: Annotated[
        str,
        Field(
            default="INFO",
            description="Log level for OpenTelemetry logging.",
            examples=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        ),
    ]
    endpoint: Annotated[
        str,
        Field(
            default="http://localhost:4317",
            description=(
                "OTLP (OpenTelemetry Protocol) endpoint for exporting telemetry data. "
                "Should include the host and port of the OTLP receiver."
            ),
            examples=["http://localhost:4317", "http://otel-collector:4317"],
        ),
    ]


class ServiceDiscoveryConfig(BaseSchema):
    type: Annotated[
        ServiceDiscoveryType,
        Field(
            default=ServiceDiscoveryType.REDIS,
            description="Type of service discovery to use.",
            examples=[item.value for item in ServiceDiscoveryType],
        ),
    ]


class ProxyCoordinatorConfig(BaseSchema):
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
            examples=["/run/backend.ai/appproxy/coordinator.pid"],
        ),
    ]

    id: Annotated[str, Field(default=f"i-{socket.gethostname()}", description="Node id.")]
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

    bind_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="0.0.0.0", port=10200),
            description="Hostname and port number coordinator API server will listen to.",
        ),
    ]
    advertised_addr: Annotated[
        HostPortPair | None,
        Field(
            default=None,
            description="Hostname and port number coordinator API server will try to connect to.",
        ),
    ]

    distributed_lock: Annotated[
        DistributedLock,
        Field(
            default=DistributedLock.PG_ADVISORY,
            description="Connection backend of the distribution lock used in coordinator.",
        ),
    ]
    redlock_config: Annotated[
        RedisLockConfig, Field(default=RedisLockConfig(), description="Redis lock configuration")
    ]

    tls_listen: Annotated[bool, Field(default=False, description="Opt in to HTTPS setup.")]
    tls_cert: Annotated[
        FilePath | None,
        Field(
            default=None,
            description="Path to TLS certificate PEM.",
            examples=["/etc/backend.ai/tls/cert.pem"],
        ),
    ]
    tls_privkey: Annotated[
        FilePath | None,
        Field(
            default=None,
            description="Path to TLS private key PEM.",
            examples=["/etc/backend.ai/tls/privkey.pem"],
        ),
    ]
    tls_advertised: Annotated[
        bool,
        Field(
            default=False,
            description="Must be active if proxy coordinator is served behind external TLS terminator.",
        ),
    ]

    allow_unauthorized_configure_request: Annotated[
        bool,
        Field(
            default=False,
            description="Do not require access token on /v2/conf request. Must not be set true unless using outdated Backend.AI cluster.",
        ),
    ]

    use_experimental_redis_event_dispatcher: Annotated[
        bool,
        Field(
            default=False,
            description="Use experimental Redis event dispatcher implementation.",
        ),
    ]

    enable_traefik: Annotated[
        bool,
        Field(
            default=False,
            description="Use traefik as proxy worker's data plane.",
        ),
    ]
    traefik: Annotated[TraefikConfig | None, Field(default=None)]

    worker_heartbeat_timeout: Annotated[
        float,
        Field(
            default=30.0,
            description="Lifetime for each worker. At the time of proxy initiation request, workers which have heartbeat timestamp older than this threshold will be excluded from scheduling.",
        ),
    ]
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
    unused_circuit_collection_timeout: Annotated[
        int,
        Field(
            default=3600,
            description="Grace period for inactive circuits. Circuits who did not report any traffics for that amount of time will be shut. Not applicable for inference circuits.",
        ),
    ]

    metric_access_allowed_hosts: str = Field(
        default="127.0.0.1/32",
        description="Limits access to `/metrics` HTTP resources from described hosts only.",
    )

    health_check_timer_interval: Annotated[
        float,
        Field(
            default=30.0,
            description="Interval in seconds for model service health check timer",
        ),
    ]

    announce_addr: Annotated[
        HostPortPair,
        Field(
            default_factory=lambda: HostPortPair(host="127.0.0.1", port=10200),
            description=("Manually set the announced address for service discovery. "),
        ),
    ]

    @property
    def advertise_base_url(self) -> str:
        """
        Generate the full advertise URL with protocol.
        Uses advertised_addr if set, otherwise falls back to bind_addr.
        Protocol is determined by tls_advertised or tls_listen flags.
        """
        connection_info = (
            self.advertised_addr if self.advertised_addr is not None else self.bind_addr
        )
        if connection_info.host_set_with_protocol:
            return f"{connection_info.host}:{connection_info.port}"
        protocol = "https" if (self.tls_advertised or self.tls_listen) else "http"
        return f"{protocol}://{connection_info.host}:{connection_info.port}"


class ServerConfig(BaseSchema):
    db: DBConfig
    redis: RedisConfig
    core_redis: Annotated[
        RedisConfig | None,
        Field(
            default=None,
            description="Redis configuration for Backend.AI event publishing. Required if appproxy's primary redis backend differs from core's one.",
        ),
    ] = None
    proxy_coordinator: ProxyCoordinatorConfig
    profiling: Annotated[ProfilingConfig, Field(default_factory=lambda: ProfilingConfig())]
    secrets: SecretConfig
    permit_hash: PermitHashConfig
    logging: LoggingConfig
    debug: DebugConfig
    otel: Annotated[
        OTELConfig,
        Field(
            default_factory=lambda: OTELConfig(
                enabled=False, log_level="INFO", endpoint="http://localhost:4317"
            )
        ),
    ]
    service_discovery: Annotated[
        ServiceDiscoveryConfig,
        Field(default_factory=lambda: ServiceDiscoveryConfig(type=ServiceDiscoveryType.REDIS)),
    ]


def load(config_path: Path | None = None, log_level: LogLevel = LogLevel.NOTSET) -> ServerConfig:
    # Determine where to read configuration.
    raw_cfg, _ = config.read_from_file(config_path, "app-proxy-coordinator")

    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogLevel.DEBUG)
    if log_level != LogLevel.NOTSET:
        config.override_key(raw_cfg, ("logging", "level"), log_level)
        config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-copmatible)
    try:
        server_config = ServerConfig(**raw_cfg)
        if server_config.profiling.enable_pyroscope:
            if not server_config.profiling.pyroscope_config:
                raise ConfigValidationError("Pyroscope enabled but config is not populated")
            if server_config.profiling.pyroscope_config.application_name is None:
                server_config.profiling.pyroscope_config.application_name = (
                    f"proxy-coordinator-{server_config.proxy_coordinator.bind_addr.port}"
                )
        if (
            server_config.proxy_coordinator.enable_traefik
            and not server_config.proxy_coordinator.traefik
        ):
            raise ConfigValidationError("Traefik enabled but configuration is not populated")
        if server_config.debug.enabled:
            print("== Proxy Coordinator configuration ==", file=sys.stderr)
            print(pformat(server_config.model_dump()), file=sys.stderr)
    except (ValidationError, ConfigValidationError) as e:
        print(
            "ConfigurationError: Could not read or validate the manager local config:",
            file=sys.stderr,
        )
        print(pformat(e), file=sys.stderr)
        raise click.Abort()
    else:
        return server_config
