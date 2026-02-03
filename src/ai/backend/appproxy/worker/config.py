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
    GroupIDValidator,
    HostPortPair,
    PermitHashConfig,
    ProfilingConfig,
    RedisConfig,
    SecretConfig,
    UserIDValidator,
)
from ai.backend.appproxy.common.errors import ConfigValidationError
from ai.backend.appproxy.common.types import (
    AppMode,
    EventLoopType,
    FrontendMode,
    FrontendServerMode,
    ProxyProtocol,
)
from ai.backend.common import config
from ai.backend.common.configs import (
    EtcdConfig,
    OTELConfig,
    PyroscopeConfig,
    ServiceDiscoveryConfig,
)
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
from ai.backend.common.typed_validators import AutoDirectoryPath
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


class AppFilterConfig(BaseSchema):
    key: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The attribute key used to match applications for filtering. "
                "Common keys include 'session.id', 'user.uuid', or 'app.name'. "
                "Used with 'value' to route specific traffic to this worker."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="session.id", prod="session.id"),
        ),
    ]
    value: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The value that must match the filter key for an application to be proxied by this worker. "
                "Works in conjunction with the filter 'key' to select specific traffic."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="test-session-id", prod="prod-session-id"),
        ),
    ]


class WildcardDomainConfig(BaseSchema):
    bind_addr: Annotated[
        HostPortPair,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The network address and port where the wildcard domain proxy server listens. "
                "This enables subdomain-based routing where each session gets a unique subdomain "
                "(e.g., session-abc.proxy.example.com)."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="127.0.0.1:10205", prod="0.0.0.0:10205"),
        ),
    ]
    domain: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The base wildcard domain suffix for routing. Must start with a dot. "
                "The proxy creates subdomains under this domain for each proxied application "
                "(e.g., '.proxy.backend.ai' enables 'app123.proxy.backend.ai')."
            ),
            added_version="25.9.0",
            example=ConfigExample(
                local=".local.proxy.backend.ai", prod=".example.proxy.backend.ai"
            ),
        ),
    ]
    advertised_port: Annotated[
        int | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "The externally accessible port number when the worker is behind NAT or a load balancer. "
                "Required when the external port differs from the bind_addr port. "
                "Leave empty if the worker is directly accessible."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="", prod="10205"),
        ),
    ]


class PortProxyConfig(BaseSchema):
    bind_host: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The host address for the port-based proxy to listen on. Use '0.0.0.0' to listen on "
                "all network interfaces, or specify a specific IP to restrict access. "
                "Port-based proxying assigns each session a unique port number."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="127.0.0.1", prod="0.0.0.0"),
        ),
    ]
    advertised_host: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "The externally accessible hostname for the port proxy when behind NAT or load balancer. "
                "Clients use this hostname to connect to proxied applications. "
                "Leave empty if the worker is directly accessible at bind_host."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="", prod="worker.example.com"),
        ),
    ]
    bind_port_range: Annotated[
        tuple[int, int],
        Field(),
        BackendAIConfigMeta(
            description=(
                "The range of ports (min, max) that can be allocated for proxied applications. "
                "Each proxied session gets a unique port from this range. Ensure the range is large "
                "enough for your expected concurrent sessions and firewall rules allow access."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="10205,10300", prod="10205,10300"),
        ),
    ]
    advertised_port_range: Annotated[
        tuple[int, int] | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "The externally accessible port range when the worker is behind NAT or port mapping. "
                "Required when external ports differ from bind_port_range. "
                "Must be the same size as bind_port_range for correct port mapping."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="", prod="10205,10300"),
        ),
    ]


class H2Config(BaseSchema):
    nghttpx_path: Annotated[
        FilePath,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The absolute filesystem path to the nghttpx binary. nghttpx is used for HTTP/2 "
                "proxy support in Backend.AI. Ensure the binary is installed and executable. "
                "Install via package manager or build from nghttp2 source."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="/usr/local/bin/nghttpx", prod="/usr/local/bin/nghttpx"),
        ),
    ]
    api_port_pool: Annotated[
        tuple[int, int],
        Field(default=(50000, 60000)),
        BackendAIConfigMeta(
            description=(
                "The port range (min, max) for nghttpx internal API communication. "
                "These ports are used for the worker to communicate with nghttpx instances. "
                "Should not overlap with other service ports on the same host."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="50000,60000", prod="50000,60000"),
        ),
    ]


class TraefikPortProxyConfig(BaseSchema):
    advertised_host: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The hostname that clients should use to connect to Traefik-proxied applications. "
                "This should be the externally accessible hostname where Traefik routes traffic. "
                "Used when Traefik handles port-based routing for the proxy worker."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="127.0.0.1", prod="worker.example.com"),
        ),
    ]
    port_range: Annotated[
        tuple[int, int],
        Field(),
        BackendAIConfigMeta(
            description=(
                "The range of ports (min, max) that Traefik can use for port-based application proxying. "
                "Traefik allocates ports from this range for each proxied application. "
                "Configure corresponding Traefik entrypoints for each port in this range."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="10205,10300", prod="10205,10300"),
        ),
    ]


class TraefikWildcardDomainConfig(BaseSchema):
    domain: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The base wildcard domain for Traefik-based subdomain routing. Must start with a dot. "
                "Traefik creates dynamic subdomains under this domain for each proxied application "
                "(e.g., '.proxy.backend.ai' enables 'app123.proxy.backend.ai')."
            ),
            added_version="25.9.0",
            example=ConfigExample(
                local=".local.proxy.backend.ai", prod=".example.proxy.backend.ai"
            ),
        ),
    ]
    advertised_port: Annotated[
        int,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The port number that clients use to access Traefik wildcard domains. "
                "Typically 443 for HTTPS or 80 for HTTP. This should match the port where Traefik "
                "is configured to receive wildcard domain traffic."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="443", prod="443"),
        ),
    ]
    tls_advertised: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Set to true if Traefik provides TLS termination for wildcard domain traffic. "
                "When enabled, the proxy worker advertises HTTPS URLs to clients. "
                "Requires proper TLS certificate configuration in Traefik."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]


class TraefikConfig(BaseSchema):
    api_port: Annotated[
        int,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The port number where Traefik's API/dashboard is accessible. "
                "The proxy worker uses this port to communicate with Traefik for dynamic configuration. "
                "Ensure this matches your Traefik's api entrypoint configuration."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="8080", prod="8080"),
        ),
    ]
    frontend_mode: Annotated[
        FrontendMode,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The routing mode for Traefik-based proxying. 'wildcard' uses subdomain-based routing "
                "(e.g., app123.proxy.example.com), 'port' uses port-based routing "
                "(e.g., proxy.example.com:12345). Choose based on your network and DNS setup."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="wildcard", prod="wildcard"),
        ),
    ]
    wildcard_domain: Annotated[
        TraefikWildcardDomainConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for Traefik wildcard domain routing. Required when frontend_mode is 'wildcard'. "
                "Defines the base domain and TLS settings for subdomain-based application routing."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    port_proxy: Annotated[
        TraefikPortProxyConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for Traefik port-based routing. Required when frontend_mode is 'port'. "
                "Defines the port range and hostname for port-based application routing."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    last_used_time_marker_directory: Annotated[
        AutoDirectoryPath,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The directory where the worker stores timestamp files tracking last activity for each "
                "proxied application. Used to determine when circuits can be garbage collected. "
                "Ensure the worker process has write permissions to this directory."
            ),
            added_version="25.9.0",
            example=ConfigExample(
                local="/tmp/backend.ai/appproxy/worker", prod="/var/lib/backend.ai/appproxy/worker"
            ),
        ),
    ]

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


class ProxyWorkerConfig(BaseSchema):
    ipc_base_path: Annotated[
        Path,
        Field(default=Path("/tmp/backend.ai/ipc")),
        BackendAIConfigMeta(
            description=(
                "The directory path where the proxy worker stores temporary UNIX domain sockets "
                "for inter-process communication. These sockets handle internal coordination "
                "between worker components. Ensure the directory exists and has appropriate permissions."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="/tmp/backend.ai/ipc", prod="/var/run/backend.ai/ipc"),
        ),
    ]
    event_loop: Annotated[
        EventLoopType,
        Field(default=EventLoopType.UVLOOP),
        BackendAIConfigMeta(
            description=(
                "The Python async event loop implementation to use. 'uvloop' provides better performance "
                "and is recommended for all deployments. 'asyncio' is the standard library fallback "
                "if uvloop is not available."
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
                "The file path where the worker writes its process ID (PID). "
                "Used by process managers (like systemd) to track and manage the service. "
                "Set to /dev/null to disable PID file creation in development environments."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="/dev/null", prod="/run/backend.ai/appproxy/worker.pid"),
        ),
    ]

    id: Annotated[
        str,
        Field(default=f"i-{socket.gethostname()}"),
        BackendAIConfigMeta(
            description=(
                "A unique identifier for this proxy worker instance. Used for logging, monitoring, "
                "and distinguishing between multiple worker instances in a cluster. "
                "Defaults to the hostname with 'i-' prefix."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="i-localhost", prod="i-worker-01"),
        ),
    ]
    user: Annotated[
        int,
        UserIDValidator,
        Field(default_factory=_get_default_uid, ge=0),
        BackendAIConfigMeta(
            description=(
                "The UNIX user ID (UID) that the worker process should run as. "
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
                "The UNIX group ID (GID) that the worker process should run as. "
                "Should be set to a group with appropriate permissions for accessing "
                "required files and sockets."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="1000", prod="1000"),
        ),
    ]

    api_bind_addr: Annotated[
        HostPortPair,
        Field(default=HostPortPair(host="0.0.0.0", port=10201)),
        BackendAIConfigMeta(
            description=(
                "The network address and port where the worker's internal API server listens. "
                "This API is used by the coordinator to manage the worker. Use '0.0.0.0' to listen "
                "on all interfaces, or specify a specific IP for security."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="0.0.0.0:10201", prod="0.0.0.0:10201"),
        ),
    ]
    api_advertised_addr: Annotated[
        HostPortPair | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "The external address that the coordinator should use to reach this worker's API. "
                "Required when the worker is behind NAT or a load balancer where the bind address "
                "differs from the externally accessible address."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="", prod="worker.example.com:10201"),
        ),
    ]

    coordinator_endpoint: Annotated[
        AnyUrl,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The HTTP(S) URL of the proxy coordinator's API endpoint. The worker connects to this "
                "endpoint to register itself, receive proxy configuration updates, and report status. "
                "Use https:// in production for secure communication."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="http://127.0.0.1:10200", prod="https://coordinator:10200"),
        ),
    ]
    verify_coordinator_ssl_certificate: Annotated[
        bool,
        Field(default=True),
        BackendAIConfigMeta(
            description=(
                "Whether to validate the coordinator's TLS/SSL certificate when connecting via HTTPS. "
                "Set to false only in development with self-signed certificates. "
                "Always enable in production to prevent man-in-the-middle attacks."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]

    authority: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description=(
                "A unique, human-readable identifier for this proxy worker's authority domain. "
                "In high-availability setups with multiple workers behind a load balancer, "
                "all workers serving the same endpoint must share the same authority value."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="worker-local", prod="worker-1"),
        ),
    ]

    use_experimental_redis_event_dispatcher: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable the experimental Redis-based event dispatcher for real-time event "
                "propagation from the coordinator. This feature is under development "
                "and may have stability issues. Use with caution in production."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]

    tls_listen: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable HTTPS/TLS for the worker's API server and proxy connections. "
                "When enabled, requires tls_cert and tls_privkey to be configured. "
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
                "the worker. For production, use certificates from a trusted CA."
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
                "Set to true when the worker is behind a TLS-terminating load balancer or "
                "reverse proxy (e.g., nginx, HAProxy). This tells the worker to advertise "
                "HTTPS URLs even though it receives unencrypted traffic from the proxy."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]

    aiomonitor_termui_port: Annotated[
        int,
        Field(default=48600, gt=0, lt=65536),
        BackendAIConfigMeta(
            description=(
                "The port number for the aiomonitor terminal UI debugging server. Allows real-time "
                "inspection of asyncio tasks and event loop status via a terminal interface. "
                "Useful for debugging async issues. Firewall this port in production."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="48600", prod="48600"),
        ),
    ]
    aiomonitor_webui_port: Annotated[
        int,
        Field(default=49600, gt=0, lt=65536),
        BackendAIConfigMeta(
            description=(
                "The port number for the aiomonitor web-based debugging interface. Provides a "
                "browser-accessible dashboard for monitoring asyncio tasks and event loop metrics. "
                "Ensure this port is firewalled in production environments."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="49600", prod="49600"),
        ),
    ]

    heartbeat_period: Annotated[
        float,
        Field(default=10.0, gt=0),
        BackendAIConfigMeta(
            description=(
                "The interval in seconds between heartbeat messages sent to the coordinator. "
                "The coordinator uses these heartbeats to detect worker failures. "
                "Must be shorter than the coordinator's worker_heartbeat_timeout setting."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="10.0", prod="10.0"),
        ),
    ]

    frontend_mode: Annotated[
        FrontendServerMode,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The routing mode for this proxy worker. 'wildcard' uses subdomain-based routing, "
                "'port' uses port-based routing, 'traefik' delegates routing to Traefik. "
                "Choose based on your network infrastructure and DNS capabilities."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="wildcard", prod="wildcard"),
        ),
    ]
    protocol: Annotated[
        ProxyProtocol,
        Field(),
        BackendAIConfigMeta(
            description=(
                "The protocol to use for proxied connections. 'http' for HTTP/1.1 traffic, "
                "'h2' for HTTP/2 traffic (requires http2 config), 'tcp' for raw TCP proxying. "
                "'grpc' is not directly supported; use 'h2' instead for gRPC traffic."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="http", prod="http"),
        ),
    ]
    wildcard_domain: Annotated[
        WildcardDomainConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for wildcard domain routing. Required when frontend_mode is 'wildcard'. "
                "Defines the bind address, base domain, and port settings for subdomain-based routing."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    port_proxy: Annotated[
        PortProxyConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for port-based routing. Required when frontend_mode is 'port'. "
                "Defines the host, port ranges, and advertised addresses for port-based routing."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    traefik: Annotated[
        TraefikConfig | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for Traefik-delegated routing. Required when frontend_mode is 'traefik'. "
                "The worker configures Traefik dynamically instead of handling routing directly."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    http2: Annotated[
        H2Config | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Configuration for HTTP/2 protocol support using nghttpx. Required when protocol is 'h2'. "
                "Defines the nghttpx binary path and API port pool for HTTP/2 proxying."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]

    accepted_traffics: Annotated[
        list[AppMode],
        Field(),
        BackendAIConfigMeta(
            description=(
                "The types of traffic this worker accepts. Use 'interactive' for user-facing "
                "applications (Jupyter, VSCode, etc.) and 'inference' for model serving endpoints. "
                "Separate workers for each traffic type enables specialized scaling."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="interactive,inference", prod="interactive,inference"),
        ),
    ]
    app_filters: Annotated[
        list[AppFilterConfig],
        Field(default_factory=list),
        BackendAIConfigMeta(
            description=(
                "Filter rules to route specific applications to this worker. Each filter matches "
                "applications by key-value pairs. Useful for routing specific sessions or users "
                "to dedicated workers for isolation or performance."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    filtered_apps_only: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "When enabled, this worker only proxies applications that match the defined app_filters. "
                "When disabled (default), the worker accepts all traffic matching accepted_traffics. "
                "Use with app_filters to create dedicated workers for specific applications."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="false", prod="false"),
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

    inference_metric_collection_interval: Annotated[
        float,
        Field(default=5.0),
        BackendAIConfigMeta(
            description=(
                "The interval in seconds between collecting metrics from inference model endpoints. "
                "Metrics include request counts, latencies, and throughput. Lower values provide "
                "more granular data but increase overhead on model services."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="5.0", prod="5.0"),
        ),
    ]

    client_pool_cleanup_interval: Annotated[
        float,
        Field(default=60.0),
        BackendAIConfigMeta(
            description=(
                "The interval in seconds for cleaning up idle HTTP client sessions. "
                "The worker maintains a pool of aiohttp.ClientSession instances for backend connections. "
                "Periodic cleanup prevents resource leaks from accumulated idle connections."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="60.0", prod="60.0"),
        ),
    ]

    announce_addr: Annotated[
        HostPortPair | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "The address this worker announces to the service discovery system. "
                "Other components use this address to locate and connect to the worker. "
                "If not set, defaults to api_bind_addr. Required when behind NAT or containers."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="", prod="worker.example.com:10201"),
        ),
    ]

    @model_validator(mode="after")
    def populate_announce_addr(self) -> Self:
        if self.announce_addr is None:
            self.announce_addr = self.api_bind_addr
        return self

    @model_validator(mode="after")
    def validate_metric_access_allowed_hosts(self) -> Self:
        try:
            ipaddress.IPv4Network(self.metric_access_allowed_hosts)
        except ValueError as e:
            raise ValueError(
                "metric_access_allowed_hosts should be either a valid IPv4 Address or Network"
            ) from e
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
    redis: Annotated[
        RedisConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Redis configuration for the proxy worker's internal operations including "
                "caching, pub/sub messaging for real-time updates, and session state management."
            ),
            added_version="25.9.0",
            composite=CompositeType.FIELD,
        ),
    ]
    proxy_worker: Annotated[
        ProxyWorkerConfig,
        Field(),
        BackendAIConfigMeta(
            description=(
                "Core proxy worker settings including network binding, TLS, routing mode, "
                "and traffic filtering configuration."
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
                "Secret keys and tokens used for authenticating requests between the worker "
                "and coordinator. Must match the secrets configured in the coordinator."
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
                "of proxy configuration requests from the coordinator."
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
                enabled=False,
                log_level="INFO",
                endpoint="http://localhost:4317",
            )
        ),
        BackendAIConfigMeta(
            description=(
                "OpenTelemetry configuration for distributed tracing and observability. "
                "Exports trace data to OTLP-compatible backends (Jaeger, Zipkin, etc.) "
                "for visualizing request flows through the proxy worker."
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
                "Service discovery configuration for locating the coordinator and other Backend.AI "
                "components. Supports Redis-based or etcd-based service registration and discovery."
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
                "etcd connection configuration for distributed coordination. "
                "Used for service discovery (if etcd-based) and shared configuration management."
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
        raise click.Abort() from e
    else:
        if server_config.debug.enabled:
            print("== Proxy Worker configuration ==", file=sys.stderr)
            print(pformat(server_config.model_dump()), file=sys.stderr)
        return server_config
