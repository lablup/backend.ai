from __future__ import annotations

import ipaddress
import os
import socket
import sys
import textwrap
from pathlib import Path
from pprint import pformat
from typing import Annotated, Self

import click
from pydantic import AnyUrl, Field, FilePath, ValidationError, model_validator

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
from ai.backend.appproxy.common.types import (
    AppMode,
    EventLoopType,
    FrontendMode,
    FrontendServerMode,
    ProxyProtocol,
)
from ai.backend.common import config
from ai.backend.common.types import ServiceDiscoveryType
from ai.backend.logging import LogLevel
from ai.backend.logging.config import LoggingConfig

_file_perm = (Path(__file__).parent / "server.py").stat()


class AppFilterConfig(BaseSchema):
    key: str
    value: str


class WildcardDomainConfig(BaseSchema):
    bind_addr: HostPortPair = Field(examples=[HostPortPair(host="127.0.0.1", port=10205)])
    domain: str = Field(
        description="Base domain for wildcard proxy.",
        examples=[".example.proxy.backend.ai"],
    )
    advertised_port: int | None = Field(
        default=None,
        description="Must be set if appproxy worker is between NAT.",
        examples=[10205],
    )


class PortProxyConfig(BaseSchema):
    bind_host: str = Field(examples=["127.0.0.1"])
    advertised_host: str | None = Field(default=None, examples=["127.0.0.1"])
    bind_port_range: tuple[int, int] = Field(examples=[(10205, 10300)])
    advertised_port_range: tuple[int, int] | None = Field(
        default=None,
        description="Must be set if appproxy worker is between NAT.",
        examples=[(10205, 10300)],
    )


class H2Config(BaseSchema):
    nghttpx_path: FilePath = Field(
        description="Path to nghttpx binary.",
        examples=[Path("/usr/local/bin/nghttpx")],
    )
    api_port_pool: tuple[int, int] = Field(
        default=(50000, 60000),
        description="Port pool for nghttpx API server.",
    )


class TraefikPortProxyConfig(BaseSchema):
    advertised_host: str = Field(examples=["127.0.0.1"])
    port_range: tuple[int, int] = Field(examples=[(10205, 10300)])


class TraefikWildcardDomainConfig(BaseSchema):
    domain: str = Field(
        description="Base domain for wildcard proxy.",
        examples=[".example.proxy.backend.ai"],
    )
    advertised_port: int
    tls_advertised: bool = Field(default=False)


class TraefikConfig(BaseSchema):
    api_port: int = Field(
        description="Port number of the `traefik` entrypoint binds.", examples=[8080]
    )
    frontend_mode: FrontendMode = Field(
        description="Type of frontend mode the worker will operate.",
        examples=[FrontendMode.WILDCARD_DOMAIN],
    )
    wildcard_domain: TraefikWildcardDomainConfig | None = Field(
        default=None,
        description="Must be filled if frontend_mode is 'wildcard'.",
    )
    port_proxy: TraefikPortProxyConfig | None = Field(
        default=None,
        description="Must be filled if frontend_mode is 'port'.",
    )
    last_used_time_marker_directory: Path = Field(
        examples=["/home/ubuntu/appproxy/worker-interactive"]
    )

    @model_validator(mode="after")
    def validate_mode_config(self) -> Self:
        match self.frontend_mode:
            case FrontendMode.PORT:
                if self.port_proxy is None:
                    raise ValueError("port_proxy must be set when frontend_mode = 'port'")
            case FrontendMode.WILDCARD_DOMAIN:
                if self.wildcard_domain is None:
                    raise ValueError("wildcard_domain must be set when frontend_mode = 'wildcard'")
        return self


class OTELConfig(BaseSchema):
    enabled: bool = Field(
        default=False,
        description=(
            "Whether to enable OpenTelemetry for tracing or logging. "
            "When enabled, traces or log will be collected and sent to the configured OTLP endpoint."
        ),
    )
    log_level: str = Field(
        default="INFO",
        description="Log level for OpenTelemetry logging.",
        examples=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    endpoint: str = Field(
        default="http://localhost:4317",
        description=(
            "OTLP (OpenTelemetry Protocol) endpoint for exporting telemetry data. "
            "Should include the host and port of the OTLP receiver."
        ),
        examples=["http://localhost:4317", "http://otel-collector:4317"],
    )


class ServiceDiscoveryConfig(BaseSchema):
    type: ServiceDiscoveryType = Field(
        default=ServiceDiscoveryType.REDIS,
        description="Type of service discovery to use.",
    )


class ProxyWorkerConfig(BaseSchema):
    ipc_base_path: Path = Field(
        default=Path("/tmp/backend.ai/ipc"),
        description="Directory to store temporary UNIX sockets.",
    )
    event_loop: EventLoopType = Field(
        default=EventLoopType.UVLOOP,
        description="Type of event loop to use.",
    )
    pid_file: Path = Field(
        default=Path(os.devnull),
        description="Place to store process PID.",
        examples=["/run/backend.ai/appproxy/coordinator.pid"],
    )

    id: str = Field(
        default=f"i-{socket.gethostname()}",
        description="Node id.",
    )
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

    api_bind_addr: HostPortPair = Field(
        default=HostPortPair(host="0.0.0.0", port=10201),
        description="Hostname and port number worker API server will listen to.",
    )
    api_advertised_addr: HostPortPair | None = Field(
        default=None,
        description="Hostname and port number which API users can access.",
        examples=[HostPortPair(host="127.0.0.1", port=10201)],
    )

    coordinator_endpoint: AnyUrl = Field(
        description="HTTP(S) URI to coordinator API endpoint.",
        examples=["http://127.0.0.1:10200"],
    )
    verify_coordinator_ssl_certificate: bool = Field(
        default=True,
        description="Validate coordinator's SSL certificate",
    )

    authority: str = Field(
        description=(
            "Unique, human-readable appproxy worker identifier. "
            "Must be set equal across every worker nodes representing same worker port via High-Availability setup."
        ),
        examples=["worker-1"],
    )

    use_experimental_redis_event_dispatcher: bool = Field(
        default=False,
        description="Use experimental Redis event dispatcher implementation.",
    )

    tls_listen: bool = Field(default=False, description="Opt in to HTTPS setup.")
    tls_cert: FilePath | None = Field(
        default=None,
        description="Path to TLS certificate PEM.",
        examples=["/etc/backend.ai/tls/cert.pem"],
    )
    tls_privkey: FilePath | None = Field(
        default=None,
        description="Path to TLS private key PEM.",
        examples=["/etc/backend.ai/tls/privkey.pem"],
    )
    tls_advertised: bool = Field(
        default=False,
        description="Must be active if proxy coordinator is served behind external TLS terminator.",
    )

    aiomonitor_termui_port: int = Field(
        default=48600,
        description="Port number for aiomonitor termui server.",
        gt=0,
        lt=65536,
    )
    aiomonitor_webui_port: int = Field(
        default=49600,
        description="Port number for aiomonitor webui server.",
        gt=0,
        lt=65536,
    )

    heartbeat_period: float = Field(
        description="Heartbeat period in seconds.",
        default=10.0,
        gt=0,
    )

    frontend_mode: FrontendServerMode = Field(
        description="Type of frontend mode the worker will operate.",
    )
    protocol: ProxyProtocol = Field(
        description="Type of protocol worker will serve. `HTTP2` not allowed here.",
    )
    wildcard_domain: WildcardDomainConfig | None = Field(
        default=None, description="Must be filled if frontend_mode is 'wildcard'."
    )
    port_proxy: PortProxyConfig | None = Field(
        default=None, description="Must be filled if frontend_mode is 'port'."
    )
    traefik: TraefikConfig | None = Field(
        default=None, description="Must be filled if frontend_mode is 'traefik'."
    )
    http2: H2Config | None = Field(
        default=None, description="Must be filled if protocol is 'http2'."
    )

    accepted_traffics: list[AppMode] = Field(
        description="Limit only selected kind of traffics to walk through this worker.",
    )
    app_filters: list[AppFilterConfig] = Field(
        default_factory=list,
        description="Define app filters.",
        examples=[
            [AppFilterConfig(key="session.id", value="CED03BE1-3ABE-4FAB-A23B-5CC9ABC60A04")]
        ],
    )
    filtered_apps_only: bool = Field(
        default=False,
        description="If active, only apps matching defined filters will be allowed to be proxied by this worker.",
    )

    metric_access_allowed_hosts: str = Field(
        default="127.0.0.1/32",
        description="Limits access to `/metrics` HTTP resources from described hosts only.",
    )

    inference_metric_collection_interval: float = Field(
        default=5.0,
        description="The interval of inference metric collection (secs)",
    )

    client_pool_cleanup_interval: float = Field(
        default=60.0,
        description="The interval to sweep unused aiohttp.ClientSession instances to make backend requests to kernel apps (secs)",
    )

    announce_addr: HostPortPair | None = Field(
        default=None,
        description=(
            "The announced address for service discovery. "
            "If not set, it will use api_bind_addr for announcement."
        ),
    )

    @model_validator(mode="after")
    def populate_announce_addr(self) -> Self:
        if self.announce_addr is None:
            self.announce_addr = self.api_bind_addr
        return self

    @model_validator(mode="after")
    def validate_metric_access_allowed_hosts(self) -> Self:
        try:
            ipaddress.IPv4Network(self.metric_access_allowed_hosts)
        except ValueError:
            raise ValueError(
                "metric_access_allowed_hosts should be either a valid IPv4 Address or Network"
            ) from None
        return self

    @model_validator(mode="after")
    def validate_mode_config(self) -> Self:
        match self.frontend_mode:
            case FrontendServerMode.PORT:
                if self.port_proxy is None:
                    raise ValueError("port_proxy must be set when frontend_mode = 'port'")
            case FrontendServerMode.WILDCARD_DOMAIN:
                if self.wildcard_domain is None:
                    raise ValueError("wildcard_domain must be set when frontend_mode = 'wildcard'")
            case FrontendServerMode.TRAEFIK:
                if self.traefik is None:
                    raise ValueError("traefik must be set when frontend_mode = 'traefik'")
        return self

    @model_validator(mode="after")
    def validate_protocol_config(self) -> Self:
        match self.protocol:
            case ProxyProtocol.GRPC:
                raise ValueError(
                    "Directly setting protocol = 'grpc' is not supported; use 'h2' instead"
                )
            case ProxyProtocol.HTTP2:
                if not self.http2:
                    raise ValueError("http2 config must be set when protocol = 'h2'")
        return self


class ServerConfig(BaseSchema):
    redis: RedisConfig
    proxy_worker: ProxyWorkerConfig
    profiling: ProfilingConfig = Field(default_factory=lambda: ProfilingConfig())
    secrets: SecretConfig
    permit_hash: PermitHashConfig
    logging: LoggingConfig
    debug: DebugConfig
    otel: OTELConfig = Field(
        default_factory=lambda: OTELConfig(
            enabled=False,
            log_level="INFO",
            endpoint="http://localhost:4317",
        )
    )
    service_discovery: ServiceDiscoveryConfig = Field(
        default_factory=lambda: ServiceDiscoveryConfig(type=ServiceDiscoveryType.REDIS)
    )


def load(config_path: Path | None = None, log_level: LogLevel = LogLevel.NOTSET) -> ServerConfig:
    # Determine where to read configuration.
    raw_cfg, _ = config.read_from_file(config_path, "app-proxy-worker")

    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogLevel.DEBUG)
    if log_level != LogLevel.NOTSET:
        config.override_key(raw_cfg, ("logging", "level"), log_level)
        config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-copmatible)
    try:
        server_config = ServerConfig.model_validate(raw_cfg)
        if server_config.profiling.enable_pyroscope:
            if not server_config.profiling.pyroscope_config:
                raise ConfigValidationError("Pyroscope enabled but config is not populated")
            if server_config.profiling.pyroscope_config.application_name is None:
                server_config.profiling.pyroscope_config.application_name = f"proxy-worker-{server_config.proxy_worker.authority}-{server_config.proxy_worker.api_bind_addr.port}"
    except (ValidationError, ConfigValidationError) as e:
        print(
            "ConfigurationError: Could not read or validate the manager local config:",
            file=sys.stderr,
        )
        if isinstance(e, ValidationError):
            detail = str(e)
        else:
            detail = pformat(e)
        print(textwrap.indent(detail, prefix="  "), file=sys.stderr)
        raise click.Abort()
    else:
        if server_config.debug.enabled:
            print("== Proxy Worker configuration ==", file=sys.stderr)
            print(pformat(server_config.model_dump()), file=sys.stderr)
        return server_config
