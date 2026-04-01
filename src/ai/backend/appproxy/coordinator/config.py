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
    GroupIDValidator,
    HostPortPair,
    PermitHashConfig,
    ProfilingConfig,
    RedisConfig,
    SecretConfig,
    UserIDValidator,
)
from ai.backend.appproxy.common.errors import ConfigValidationError
from ai.backend.appproxy.common.types import EventLoopType
from ai.backend.common import config
from ai.backend.common.configs import (
    EtcdConfig,
    OTELConfig,
    PyroscopeConfig,
    ServiceDiscoveryConfig,
)
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
from ai.backend.common.types import ServiceDiscoveryType
from ai.backend.logging import LogLevel
from ai.backend.logging.config import LoggingConfig


def _get_default_uid() -> int:
    """Get UID from server.py file in the same directory as config.py."""
    server_file = Path(__file__).parent / "server.py"
    if not server_file.exists():
        raise ConfigValidationError(f"server.py not found at {server_file}")
    return server_file.stat().st_uid


def _get_default_gid() -> int:
    """Get GID from server.py file in the same directory as config.py."""
    server_file = Path(__file__).parent / "server.py"
    if not server_file.exists():
        raise ConfigValidationError(f"server.py not found at {server_file}")
    return server_file.stat().st_gid


class DBType(enum.StrEnum):
    POSTGRESQL = "postgresql"


class DistributedLock(enum.StrEnum):
    FILELOCK = "filelock"
    PG_ADVISORY = "pg_advisory"
    REDLOCK = "redlock"


class RedisLockConfig(BaseSchema):
    lock_retry_interval: Annotated[
        float | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Retry interval in seconds for Redis lock acquisition.",
            added_version="25.9.0",
            example=ConfigExample(local="0.1", prod="0.5"),
        ),
    ]


class DBConfig(BaseSchema):
    type: Annotated[
        DBType,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The type of database backend used by the proxy coordinator. "
                "Currently only PostgreSQL is supported for storing proxy routing and circuit data."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="postgresql", prod="postgresql"),
        ),
    ]
    addr: Annotated[
        HostPortPair,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The network address (host:port) of the PostgreSQL database server. "
                "In local development, typically points to localhost. "
                "In production, should point to your PostgreSQL server or cluster endpoint."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="127.0.0.1:5432", prod="db-server:5432"),
        ),
    ]
    name: Annotated[
        str,
        Field(min_length=2, max_length=64),
        BackendAIConfigMeta(
            description=(
                "The name of the PostgreSQL database to use for the proxy coordinator. "
                "This database stores proxy routing rules, circuit states, and session mappings. "
                "Ensure this database is created before starting the coordinator."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="appproxy", prod="appproxy"),
        ),
    ]
    user: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The PostgreSQL username for database authentication. "
                "This user should have appropriate permissions to read/write "
                "to the proxy coordinator database tables."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="postgres", prod="backend"),
        ),
    ]
    password: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The password for PostgreSQL database authentication. "
                "Keep this value secure and do not expose it in logs or version control."
            ),
            added_version="25.9.0",
            secret=True,
            example=ConfigExample(local="DB_PASSWORD", prod="DB_PASSWORD"),
        ),
    ]
    pool_size: Annotated[
        int,
        Field(gt=0, default=8),
        BackendAIConfigMeta(
            description=(
                "The number of persistent database connections maintained in the connection pool. "
                "Higher values allow more concurrent database operations but consume more resources. "
                "Adjust based on expected load and available database connections."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="8", prod="32"),
        ),
    ]
    max_overflow: Annotated[
        int,
        Field(gt=-2, default=64),
        BackendAIConfigMeta(
            description=(
                "The maximum number of additional connections allowed beyond pool_size during peak load. "
                "These overflow connections are created on-demand and closed when no longer needed. "
                "Set to -1 for unlimited overflow, or 0 to disable overflow entirely."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="64", prod="128"),
        ),
    ]


class TraefikConfig(BaseSchema):
    etcd: Annotated[
        EtcdConfig,
        Field(default_factory=lambda: EtcdConfig(namespace="traefik")),
        BackendAIConfigMeta(
            description=(
                "Configuration for the etcd connection used by Traefik integration. "
                "Traefik uses etcd as its configuration backend to dynamically update routing rules. "
                "The namespace should be set to 'traefik' to isolate Traefik's configuration keys."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]


class ProxyCoordinatorConfig(BaseSchema):
    ipc_base_path: Annotated[
        Path,
        Field(default=Path("/tmp/backend.ai/ipc")),
        BackendAIConfigMeta(
            description=(
                "The directory path where the proxy coordinator stores temporary UNIX domain sockets "
                "for inter-process communication (IPC). These sockets are used for internal "
                "communication between coordinator components. Ensure the directory exists and "
                "has appropriate permissions."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="/tmp/backend.ai/ipc", prod="/var/run/backend.ai/ipc"),
        ),
    ]
    event_loop: Annotated[
        EventLoopType,
        Field(default=EventLoopType.ASYNCIO),
        BackendAIConfigMeta(
            description=(
                "The Python async event loop implementation to use. 'asyncio' is the standard "
                "library implementation suitable for development. 'uvloop' provides better "
                "performance and is recommended for production deployments."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="asyncio", prod="asyncio"),
        ),
    ]
    pid_file: Annotated[
        Path,
        Field(default=Path(os.devnull)),
        BackendAIConfigMeta(
            description=(
                "The file path where the coordinator writes its process ID (PID). "
                "This is used by process managers (like systemd) to track and manage the service. "
                "Set to /dev/null to disable PID file creation in development environments."
            ),
            added_version="25.9.0",
            example=ConfigExample(
                local="/dev/null", prod="/run/backend.ai/appproxy/coordinator.pid"
            ),
        ),
    ]

    id: Annotated[
        str,
        Field(default=f"i-{socket.gethostname()}"),
        BackendAIConfigMeta(
            description=(
                "A unique identifier for this proxy coordinator instance. "
                "Used for logging, monitoring, and distinguishing between multiple coordinator "
                "instances in a cluster. Defaults to the hostname with 'i-' prefix."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="i-localhost", prod="i-coordinator-01"),
        ),
    ]
    user: Annotated[
        int,
        UserIDValidator,
        Field(default_factory=_get_default_uid, ge=0),
        BackendAIConfigMeta(
            description=(
                "The UNIX user ID (UID) that the coordinator process should run as. "
                "For security, avoid running as root (UID 0) in production. "
                "The process will drop privileges to this user after startup."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="1000", prod="1000"),
        ),
    ]
    group: Annotated[
        int,
        GroupIDValidator,
        Field(default_factory=_get_default_gid, ge=0),
        BackendAIConfigMeta(
            description=(
                "The UNIX group ID (GID) that the coordinator process should run as. "
                "Should be set to a group with appropriate permissions for accessing "
                "required files and sockets."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="1000", prod="1000"),
        ),
    ]

    bind_addr: Annotated[
        HostPortPair,
        Field(default=HostPortPair(host="0.0.0.0", port=10200)),
        BackendAIConfigMeta(
            description=(
                "The network address and port where the coordinator API server listens for "
                "incoming connections. Use '0.0.0.0' to listen on all network interfaces, "
                "or specify a specific IP to restrict access. Port 10200 is the default."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="0.0.0.0:10200", prod="0.0.0.0:10200"),
        ),
    ]
    advertised_addr: Annotated[
        HostPortPair | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "The external address that workers and clients should use to connect to this "
                "coordinator. Required when the coordinator is behind a load balancer or NAT, "
                "where the bind address differs from the externally accessible address."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="", prod="coordinator.example.com:10200"),
        ),
    ]

    distributed_lock: Annotated[
        DistributedLock,
        Field(default=DistributedLock.PG_ADVISORY),
        BackendAIConfigMeta(
            description=(
                "The backend mechanism for distributed locking across multiple coordinator instances. "
                "'pg_advisory' uses PostgreSQL advisory locks (recommended), 'redlock' uses Redis-based "
                "distributed locks, 'filelock' uses filesystem locks (single-node only)."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="pg_advisory", prod="pg_advisory"),
        ),
    ]
    redlock_config: Annotated[
        RedisLockConfig,
        Field(default_factory=lambda: RedisLockConfig()),
        BackendAIConfigMeta(
            description=(
                "Configuration for Redis-based distributed locking (Redlock algorithm). "
                "Only used when distributed_lock is set to 'redlock'. Configures retry intervals "
                "and timeout behavior for lock acquisition."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]

    tls_listen: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable HTTPS/TLS for the coordinator API server. When enabled, the server "
                "will use encrypted connections. Requires tls_cert and tls_privkey to be configured. "
                "Recommended for production deployments to secure communication."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    tls_cert: Annotated[
        FilePath | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "The file path to the TLS/SSL certificate in PEM format. Required when tls_listen "
                "is enabled. The certificate should be issued for the domain/IP used to access "
                "the coordinator. For production, use certificates from a trusted CA."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="", prod="/etc/backend.ai/tls/cert.pem"),
        ),
    ]
    tls_privkey: Annotated[
        FilePath | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "The file path to the TLS/SSL private key in PEM format. Required when tls_listen "
                "is enabled. This file must be kept secure with restricted permissions (e.g., 0600). "
                "Never commit this file to version control."
            ),
            added_version="25.9.0",
            secret=True,
        ),
    ]
    tls_advertised: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Set to true when the coordinator is behind a TLS-terminating load balancer or "
                "reverse proxy (e.g., nginx, HAProxy). This tells the coordinator to advertise "
                "HTTPS URLs even though it receives unencrypted traffic from the proxy."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]

    allow_unauthorized_configure_request: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Allow configuration requests without authentication tokens. WARNING: This is a "
                "security risk and should only be enabled for backward compatibility with older "
                "Backend.AI clusters. Keep this disabled in production environments."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]

    use_experimental_redis_event_dispatcher: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable the experimental Redis-based event dispatcher for real-time event "
                "propagation between coordinator and workers. This feature is under development "
                "and may have stability issues. Use with caution in production."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]

    enable_traefik: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable Traefik integration as the proxy worker's data plane. When enabled, "
                "the coordinator will manage routing rules through Traefik instead of the built-in "
                "proxy workers. Requires Traefik to be deployed and configured separately."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    traefik: Annotated[
        TraefikConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for Traefik integration when enable_traefik is true. "
                "Includes the etcd connection settings that Traefik uses as its configuration "
                "backend. Required when enable_traefik is enabled."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]

    worker_heartbeat_timeout: Annotated[
        float,
        Field(default=30.0),
        BackendAIConfigMeta(
            description=(
                "The maximum time in seconds a worker can go without sending a heartbeat before "
                "being considered unavailable. Workers that exceed this timeout will be excluded "
                "from proxy scheduling. Increase this value in high-latency network environments."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="30.0", prod="60.0"),
        ),
    ]
    aiomonitor_termui_port: Annotated[
        int,
        Field(gt=0, lt=65536, default=48500),
        BackendAIConfigMeta(
            description=(
                "The port number for the aiomonitor terminal UI debugging server. Aiomonitor allows "
                "real-time inspection of asyncio tasks and event loop status via a terminal interface. "
                "Useful for debugging async issues. Disable in production by setting a non-accessible port."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="48500", prod="48500"),
        ),
    ]
    aiomonitor_webui_port: Annotated[
        int,
        Field(gt=0, lt=65536, default=49500),
        BackendAIConfigMeta(
            description=(
                "The port number for the aiomonitor web-based debugging interface. Unlike the terminal UI, "
                "this provides a browser-accessible dashboard for monitoring asyncio tasks and event loop "
                "metrics. Ensure this port is firewalled in production environments."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="49500", prod="49500"),
        ),
    ]
    unused_circuit_collection_timeout: Annotated[
        int,
        Field(default=3600),
        BackendAIConfigMeta(
            description=(
                "The grace period in seconds before cleaning up inactive proxy circuits. Circuits that "
                "have not reported any network traffic within this time will be automatically terminated "
                "to free resources. Set to 3600 (1 hour) by default. Does not apply to inference circuits, "
                "which have their own lifecycle management."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="3600", prod="3600"),
        ),
    ]

    metric_access_allowed_hosts: Annotated[
        str,
        Field(default="127.0.0.1/32"),
        BackendAIConfigMeta(
            description=(
                "CIDR notation specifying which IP addresses can access the /metrics HTTP endpoint. "
                "This endpoint exposes Prometheus-compatible metrics for monitoring. Restrict access "
                "to your monitoring infrastructure network in production to prevent information disclosure."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="127.0.0.1/32", prod="10.0.0.0/8"),
        ),
    ]

    health_check_timer_interval: Annotated[
        float,
        Field(default=30.0),
        BackendAIConfigMeta(
            description=(
                "The interval in seconds between health checks for model inference services. "
                "The coordinator periodically verifies that backend model services are responsive. "
                "Lower values detect failures faster but increase network overhead. "
                "Higher values reduce overhead but may delay failure detection."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="30.0", prod="30.0"),
        ),
    ]

    announce_addr: Annotated[
        HostPortPair,
        Field(default_factory=lambda: HostPortPair(host="127.0.0.1", port=10200)),
        BackendAIConfigMeta(
            description=(
                "The address this coordinator announces to the service discovery system (etcd or Redis). "
                "Other components in the cluster use this address to locate and connect to the coordinator. "
                "In containerized or NAT environments, this should be the externally routable address."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="127.0.0.1:10200", prod="coordinator.example.com:10200"),
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
    db: Annotated[
        DBConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "PostgreSQL database configuration for the proxy coordinator. "
                "Stores proxy routing rules, circuit states, and session mappings."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    redis: Annotated[
        RedisConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Redis configuration for the proxy coordinator's internal operations including "
                "caching, pub/sub messaging, and distributed locking (when using Redlock)."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    core_redis: Annotated[
        RedisConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Optional Redis configuration for connecting to the Backend.AI Manager's event bus. "
                "Only required when the proxy coordinator uses a different Redis instance than the "
                "Manager core. If not specified, the coordinator uses the 'redis' configuration above."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    proxy_coordinator: Annotated[
        ProxyCoordinatorConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Core proxy coordinator settings including network binding, TLS, distributed locking, "
                "and worker management configuration."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    profiling: Annotated[
        ProfilingConfig,
        Field(default_factory=lambda: ProfilingConfig()),
        BackendAIConfigMeta(
            description=(
                "Performance profiling configuration for debugging and optimization. "
                "Includes settings for cProfile and Pyroscope continuous profiling."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    secrets: Annotated[
        SecretConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Secret keys and tokens used for authenticating requests between the coordinator "
                "and other Backend.AI components. Must match the secrets configured in Manager."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    permit_hash: Annotated[
        PermitHashConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Configuration for permit hash validation, which verifies the authenticity "
                "of proxy configuration requests from the Backend.AI Manager."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    logging: Annotated[
        LoggingConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Logging configuration including log levels, output formats, and destinations. "
                "Supports console, file, and external log aggregation systems."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    debug: Annotated[
        DebugConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Debug mode settings for development and troubleshooting. "
                "Enables verbose logging and additional diagnostic features when enabled."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    otel: Annotated[
        OTELConfig,
        Field(
            default_factory=lambda: OTELConfig(
                enabled=False, log_level="INFO", endpoint="http://localhost:4317"
            )
        ),
        BackendAIConfigMeta(
            description=(
                "OpenTelemetry configuration for distributed tracing and observability. "
                "Exports trace data to OTLP-compatible backends (Jaeger, Zipkin, etc.) "
                "for visualizing request flows across Backend.AI components."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    service_discovery: Annotated[
        ServiceDiscoveryConfig,
        Field(default_factory=lambda: ServiceDiscoveryConfig(type=ServiceDiscoveryType.REDIS)),
        BackendAIConfigMeta(
            description=(
                "Service discovery configuration for locating other Backend.AI components in the cluster. "
                "Supports Redis-based or etcd-based service registration and discovery."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    etcd: Annotated[
        EtcdConfig,
        Field(default_factory=EtcdConfig),
        BackendAIConfigMeta(
            description=(
                "etcd connection configuration for distributed coordination and configuration management. "
                "Used for service discovery (if etcd-based) and Traefik integration."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    pyroscope: Annotated[
        PyroscopeConfig,
        Field(default_factory=PyroscopeConfig),
        BackendAIConfigMeta(
            description=(
                "Pyroscope continuous profiling configuration for production performance analysis. "
                "Sends CPU and memory profiling data to a Pyroscope server for flame graph visualization."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
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
        raise click.Abort() from e
    else:
        return server_config
