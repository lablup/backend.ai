import ipaddress
import os
import socket
import sys
from pathlib import Path
from pprint import pformat
from typing import Annotated

import click
from pydantic import AnyUrl, Field, FilePath, ValidationError

from ai.backend.appproxy.common.exceptions import ConfigValidationError
from ai.backend.common import config
from ai.backend.common.types import ServiceDiscoveryType
from ai.backend.logging import LogLevel

from ..common.config import (
    BaseSchema,
    DebugConfig,
    GroupID,
    HostPortPair,
    LoggingConfig,
    PermitHashConfig,
    ProfilingConfig,
    RedisConfig,
    SecretConfig,
    UserID,
)
from ..common.types import AppMode, EventLoopType, FrontendMode, FrontendServerMode, ProxyProtocol

_file_perm = (Path(__file__).parent / "server.py").stat()


class AppFilterConfig(BaseSchema):
    key: str
    value: str


class WildcardDomainConfig(BaseSchema):
    bind_addr: Annotated[HostPortPair, Field(examples=[HostPortPair(host="127.0.0.1", port=10205)])]
    domain: Annotated[
        str,
        Field(
            description="Base domain for wildcard proxy.", examples=[".example.proxy.backend.ai"]
        ),
    ]
    advertised_port: Annotated[
        int | None,
        Field(
            default=None,
            description="Must be set if appproxy worker is between NAT.",
            examples=[10205],
        ),
    ]


class PortProxyConfig(BaseSchema):
    bind_host: Annotated[str, Field(examples=["127.0.0.1"])]
    advertised_host: Annotated[str | None, Field(default=None, examples=["127.0.0.1"])]
    bind_port_range: Annotated[tuple[int, int], Field(examples=[(10205, 10300)])]
    advertised_port_range: Annotated[
        tuple[int, int] | None,
        Field(
            default=None,
            description="Must be set if appproxy worker is between NAT.",
            examples=[(10205, 10300)],
        ),
    ]


class H2Config(BaseSchema):
    nghttpx_path: Annotated[
        FilePath,
        Field(description="Path to nghttpx binary.", examples=[Path("/usr/local/bin/nghttpx")]),
    ]
    api_port_pool: Annotated[
        tuple[int, int],
        Field(description="Port pool for nghttpx API server.", default=(50000, 60000)),
    ]


class TraefikPortProxyConfig(BaseSchema):
    advertised_host: Annotated[str, Field(default=None, examples=["127.0.0.1"])]
    port_range: Annotated[tuple[int, int], Field(examples=[(10205, 10300)])]


class TraefikWildcardDomainConfig(BaseSchema):
    domain: Annotated[
        str,
        Field(
            description="Base domain for wildcard proxy.", examples=[".example.proxy.backend.ai"]
        ),
    ]
    advertised_port: int
    tls_advertised: Annotated[bool, Field(default=False)]


class TraefikConfig(BaseSchema):
    api_port: Annotated[
        int, Field(description="Port number of the `traefik` entrypoint binds.", examples=[8080])
    ]
    frontend_mode: Annotated[
        FrontendMode,
        Field(
            description="Type of frontend mode the worker will operate.",
            examples=[FrontendMode.WILDCARD_DOMAIN],
        ),
    ]
    wildcard_domain: Annotated[
        TraefikWildcardDomainConfig | None,
        Field(default=None, description="Must be filled if frontend_mode is 'wildcard'."),
    ]
    port_proxy: Annotated[
        TraefikPortProxyConfig | None,
        Field(default=None, description="Must be filled if frontend_mode is 'port'."),
    ]
    last_used_time_marker_directory: Annotated[
        Path, Field(examples=["/home/ubuntu/appproxy/worker-interactive"])
    ]


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


class ProxyWorkerConfig(BaseSchema):
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

    api_bind_addr: Annotated[
        HostPortPair,
        Field(
            default=HostPortPair(host="0.0.0.0", port=10201),
            description="Hostname and port number worker API server will listen to.",
        ),
    ]
    api_advertised_addr: Annotated[
        HostPortPair | None,
        Field(
            default=None,
            examples=[HostPortPair(host="127.0.0.1", port=10201)],
            description="Hostname and port number which API users can access.",
        ),
    ]
    coordinator_endpoint: Annotated[
        AnyUrl,
        Field(
            description="HTTP(S) URI to coordinator API endpoint.",
            examples=["http://127.0.0.1:10200"],
        ),
    ]
    verify_coordinator_ssl_certificate: Annotated[
        bool,
        Field(description="Validate coordinator's SSL certificate", default=True),
    ]

    authority: Annotated[
        str,
        Field(
            description="Unique, human-readable appproxy worker identifier. Must be set equal across every worker nodes representing same worker port via High-Availability setup.",
            examples=["worker-1"],
        ),
    ]

    use_experimental_redis_event_dispatcher: Annotated[
        bool,
        Field(
            default=False,
            description="Use experimental Redis event dispatcher implementation.",
        ),
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

    aiomonitor_termui_port: Annotated[
        int,
        Field(
            gt=0, lt=65536, description="Port number for aiomonitor termui server.", default=48600
        ),
    ]
    aiomonitor_webui_port: Annotated[
        int,
        Field(
            gt=0, lt=65536, description="Port number for aiomonitor webui server.", default=49600
        ),
    ]

    heartbeat_period: Annotated[
        float, Field(gt=0, description="Heartbeat period in seconds.", default=10.0)
    ]

    frontend_mode: Annotated[
        FrontendServerMode,
        Field(
            description="Type of frontend mode the worker will operate.",
            examples=[FrontendServerMode.WILDCARD_DOMAIN],
        ),
    ]
    protocol: Annotated[
        ProxyProtocol,
        Field(
            description="Type of protocol worker will serve. `HTTP2` not allowed here.",
            examples=[ProxyProtocol.HTTP],
        ),
    ]

    wildcard_domain: Annotated[
        WildcardDomainConfig | None,
        Field(default=None, description="Must be filled if frontend_mode is 'wildcard'."),
    ]
    port_proxy: Annotated[
        PortProxyConfig | None,
        Field(default=None, description="Must be filled if frontend_mode is 'port'."),
    ]
    traefik: Annotated[
        TraefikConfig | None,
        Field(default=None, description="Must be filled if frontend_mode is 'traefik'."),
    ]

    http2: Annotated[
        H2Config | None, Field(default=None, description="Must be filled if protocol is 'http2'.")
    ]

    accepted_traffics: Annotated[
        list[AppMode],
        Field(
            description="Limit only selected kind of traffics to walk through this worker.",
            examples=[[AppMode.INFERENCE, AppMode.INTERACTIVE]],
        ),
    ]
    app_filters: Annotated[
        list[AppFilterConfig],
        Field(
            description="Define app filters.",
            examples=[
                [AppFilterConfig(key="session.id", value="CED03BE1-3ABE-4FAB-A23B-5CC9ABC60A04")]
            ],
            default=[],
        ),
    ]
    filtered_apps_only: Annotated[
        bool,
        Field(
            default=False,
            description="If active, only apps matching defined filters will be allowed to be proxied by this worker.",
        ),
    ]

    metric_access_allowed_hosts: str = Field(
        default="127.0.0.1/32",
        description="Limits access to `/metrics` HTTP resources from described hosts only.",
    )

    inference_metric_collection_interval: Annotated[
        float, Field(default=5.0, description="Sets the interval of inference metric collector")
    ]

    announce_addr: Annotated[
        HostPortPair,
        Field(
            default_factory=lambda: HostPortPair(host="http://127.0.0.1", port=10201),
            description=(
                "Manually set the announced address for service discovery. "
                "If not set, it will use api_bind_addr for announcement."
            ),
        ),
    ]


class ServerConfig(BaseSchema):
    redis: RedisConfig
    proxy_worker: ProxyWorkerConfig
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
    raw_cfg, _ = config.read_from_file(config_path, "app-proxy-worker")

    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogLevel.DEBUG)
    if log_level != LogLevel.NOTSET:
        config.override_key(raw_cfg, ("logging", "level"), log_level)
        config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-copmatible)
    try:
        cfg = ServerConfig(**raw_cfg)
        try:
            ipaddress.IPv4Network(cfg.proxy_worker.metric_access_allowed_hosts)
        except ValueError:
            raise ConfigValidationError(
                "metric_access_allowed_hosts should be either a valid IPv4 Address or Network"
            )
        match cfg.proxy_worker.frontend_mode:
            case FrontendServerMode.WILDCARD_DOMAIN if not cfg.proxy_worker.wildcard_domain:
                raise ConfigValidationError("wildcard_domain mode set but config is not populated")
            case FrontendServerMode.PORT if not cfg.proxy_worker.port_proxy:
                raise ConfigValidationError("port proxy mode set but config is not populated")
            case FrontendServerMode.TRAEFIK:
                if not cfg.proxy_worker.traefik:
                    raise ConfigValidationError(
                        "traefik proxy mode set but config is not populated"
                    )
                match cfg.proxy_worker.traefik.frontend_mode:
                    case FrontendMode.PORT if not cfg.proxy_worker.traefik.port_proxy:
                        raise ConfigValidationError(
                            "port proxy mode set but config is not populated"
                        )
                    case FrontendMode.WILDCARD_DOMAIN if (
                        not cfg.proxy_worker.traefik.wildcard_domain
                    ):
                        raise ConfigValidationError(
                            "wildcard_domain mode set but config is not populated"
                        )

        if cfg.proxy_worker.protocol == ProxyProtocol.GRPC:
            raise ConfigValidationError(
                "Do not specify grpc as protocol in config; use http2 instead"
            )
        if cfg.proxy_worker.protocol == ProxyProtocol.HTTP2 and not cfg.proxy_worker.http2:
            raise ConfigValidationError("HTTP2 procotol set but config is not populated")
        if cfg.profiling.enable_pyroscope:
            if not cfg.profiling.pyroscope_config:
                raise ConfigValidationError("Pyroscope enabled but config is not populated")
            if cfg.profiling.pyroscope_config.application_name is None:
                cfg.profiling.pyroscope_config.application_name = f"proxy-worker-{cfg.proxy_worker.authority}-{cfg.proxy_worker.api_bind_addr.port}"
        if cfg.debug.enabled:
            print("== Proxy Worker configuration ==", file=sys.stderr)
            print(pformat(cfg.model_dump()), file=sys.stderr)
    except (ValidationError, ConfigValidationError) as e:
        print(
            "ConfigurationError: Could not read or validate the manager local config:",
            file=sys.stderr,
        )
        print(pformat(e), file=sys.stderr)
        raise click.Abort()
    else:
        return cfg
