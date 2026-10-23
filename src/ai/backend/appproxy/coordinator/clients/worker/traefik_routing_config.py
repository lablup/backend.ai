from __future__ import annotations

from dataclasses import dataclass
from typing import Final, NotRequired, TypedDict

from ai.backend.appproxy.common.config import PermitHashConfig, SecretConfig
from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.coordinator.config import TraefikConfig
from ai.backend.appproxy.coordinator.errors.ingress import TraefikWildcardDomainMissingError
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAuthority,
    IngressBackend,
    IngressFrontend,
    IngressFrontendKind,
    IngressKey,
    IngressProtocol,
    IngressTarget,
)

_CORS_HEADERS_MIDDLEWARE_NAME: Final[str] = "CORSHeaders"


class TraefikHttpRouterConfig(TypedDict):
    rule: str
    service: str
    entrypoints: list[str]
    middlewares: list[str]
    tls: NotRequired[str]


class TraefikTcpRouterConfig(TypedDict):
    rule: str
    service: str
    entrypoints: list[str]


class TraefikHttpServer(TypedDict):
    url: str


class TraefikHttpLoadBalancer(TypedDict):
    servers: list[TraefikHttpServer]


class TraefikHttpServiceConfig(TypedDict):
    # Left out when no target receives traffic, which clears the service.
    loadBalancer: NotRequired[TraefikHttpLoadBalancer]


class TraefikTcpServer(TypedDict):
    address: str


class TraefikTcpLoadBalancer(TypedDict):
    servers: list[TraefikTcpServer]


class TraefikTcpServiceConfig(TypedDict):
    # Left out when no target receives traffic, which clears the service.
    loadBalancer: NotRequired[TraefikTcpLoadBalancer]


class TraefikCorsHeaders(TypedDict):
    accessControlAllowHeaders: str
    accessControlAllowOriginList: list[str]


class TraefikCorsHeadersMiddlewareConfig(TypedDict):
    headers: TraefikCorsHeaders


class TraefikIpStrategy(TypedDict, total=False):
    depth: int
    excludedIPs: list[str]


class TraefikIpAllowList(TypedDict):
    sourceRange: list[str]
    ipStrategy: NotRequired[TraefikIpStrategy]


class TraefikIpAllowListMiddlewareConfig(TypedDict):
    ipAllowList: TraefikIpAllowList


class TraefikAuthPluginOptions(TypedDict):
    ingress: str
    jwt_secret: str
    permit_hash_secret: str
    permit_cookie_name: str


TraefikAuthPluginOptionsByName = TypedDict(
    "TraefikAuthPluginOptionsByName", {"appproxy-traefik-plugin": TraefikAuthPluginOptions}
)


class TraefikAuthPluginMiddlewareConfig(TypedDict):
    plugin: TraefikAuthPluginOptionsByName


type TraefikHttpMiddlewareConfig = (
    TraefikCorsHeadersMiddlewareConfig
    | TraefikIpAllowListMiddlewareConfig
    | TraefikAuthPluginMiddlewareConfig
)
type TraefikRoutingConfig = (
    TraefikHttpRouterConfig
    | TraefikTcpRouterConfig
    | TraefikHttpServiceConfig
    | TraefikTcpServiceConfig
    | TraefikHttpMiddlewareConfig
)


@dataclass(frozen=True)
class TraefikRoutingConfigFactoryArgs:
    traefik_config: TraefikConfig
    secrets: SecretConfig
    permit_hash: PermitHashConfig


class TraefikRoutingConfigFactory:
    """Builds the Traefik router, middleware and service configs of an ingress and the etcd keys
    Traefik reads them from."""

    _traefik_config: TraefikConfig
    _secrets: SecretConfig
    _permit_hash: PermitHashConfig

    def __init__(self, args: TraefikRoutingConfigFactoryArgs) -> None:
        self._traefik_config = args.traefik_config
        self._secrets = args.secrets
        self._permit_hash = args.permit_hash

    @classmethod
    def all_routing_config_etcd_keys(cls, ingress_key: IngressKey) -> list[str]:
        """Every routing config key an ingress can own, for clearing the ones it no longer has."""
        return [
            cls._router_etcd_key(ingress_key, IngressProtocol.HTTP),
            cls._service_etcd_key(ingress_key, IngressProtocol.HTTP),
            cls._http_middleware_etcd_key(
                ingress_key.authority, cls._ip_allowlist_middleware_name(ingress_key)
            ),
            cls._http_middleware_etcd_key(
                ingress_key.authority, cls._auth_plugin_middleware_name(ingress_key)
            ),
            cls._router_etcd_key(ingress_key, IngressProtocol.TCP),
            cls._service_etcd_key(ingress_key, IngressProtocol.TCP),
        ]

    def routing_configs_by_etcd_key(
        self, ingress: Ingress, *, hostname: str, wildcard_domain: str | None, tls_listen: bool
    ) -> dict[str, TraefikRoutingConfig]:
        """Router, service and middleware configs of the ingress, by the etcd key Traefik reads."""
        ingress_key = ingress.key()
        frontend_protocol = ingress.frontend.protocol
        router_etcd_key = self._router_etcd_key(ingress_key, frontend_protocol)
        service_etcd_key = self._service_etcd_key(ingress_key, frontend_protocol)
        match frontend_protocol:
            case IngressProtocol.TCP:
                return {
                    router_etcd_key: self._tcp_router_config(ingress),
                    service_etcd_key: self._tcp_service_config(ingress.backend),
                }
            case IngressProtocol.HTTP | IngressProtocol.HTTP2:
                return {
                    router_etcd_key: self._http_router_config(
                        ingress,
                        host_rule=self._host_rule(
                            ingress, hostname=hostname, wildcard_domain=wildcard_domain
                        ),
                        tls_listen=tls_listen,
                    ),
                    service_etcd_key: self._http_service_config(ingress.backend),
                    **self._http_middleware_configs(ingress),
                }

    @classmethod
    def _router_etcd_key(cls, ingress_key: IngressKey, protocol: IngressProtocol) -> str:
        traefik_protocol_key = cls._traefik_protocol_key(protocol)
        return (
            f"worker_{ingress_key.authority}/{traefik_protocol_key}/routers/"
            f"{cls._router_name(ingress_key)}"
        )

    @classmethod
    def _service_etcd_key(cls, ingress_key: IngressKey, protocol: IngressProtocol) -> str:
        traefik_protocol_key = cls._traefik_protocol_key(protocol)
        return (
            f"worker_{ingress_key.authority}/{traefik_protocol_key}/services/"
            f"{cls._service_name(ingress_key)}"
        )

    @classmethod
    def _http_router_config(
        cls, ingress: Ingress, *, host_rule: str, tls_listen: bool
    ) -> TraefikHttpRouterConfig:
        ingress_key = ingress.key()
        # The ipAllowList middleware must precede the auth plugin so that disallowed
        # clients are rejected before any credential handling.
        middleware_names = [_CORS_HEADERS_MIDDLEWARE_NAME]
        if ingress.access.allowed_client_ips:
            middleware_names.append(cls._ip_allowlist_middleware_name(ingress_key))
        middleware_names.append(cls._auth_plugin_middleware_name(ingress_key))
        router_config: TraefikHttpRouterConfig = {
            "rule": host_rule,
            "service": cls._service_name(ingress_key),
            "entrypoints": [cls._entrypoint_name(ingress.frontend)],
            "middlewares": middleware_names,
        }
        if tls_listen:
            router_config["tls"] = ""
        return router_config

    @classmethod
    def _tcp_router_config(cls, ingress: Ingress) -> TraefikTcpRouterConfig:
        return {
            "rule": cls._client_ip_rule(ingress.access),
            "service": cls._service_name(ingress.key()),
            "entrypoints": [cls._entrypoint_name(ingress.frontend)],
        }

    def _http_middleware_configs(self, ingress: Ingress) -> dict[str, TraefikHttpMiddlewareConfig]:
        ingress_key = ingress.key()
        cors_headers_etcd_key = self._http_middleware_etcd_key(
            ingress.authority, _CORS_HEADERS_MIDDLEWARE_NAME
        )
        middleware_configs: dict[str, TraefikHttpMiddlewareConfig] = {
            cors_headers_etcd_key: {
                "headers": {
                    "accessControlAllowHeaders": "*",
                    "accessControlAllowOriginList": ["*"],
                },
            },
        }
        if ingress.access.allowed_client_ips:
            ip_allowlist_etcd_key = self._http_middleware_etcd_key(
                ingress.authority, self._ip_allowlist_middleware_name(ingress_key)
            )
            middleware_configs[ip_allowlist_etcd_key] = self._ip_allowlist_middleware_config(
                ingress.access
            )
        auth_plugin_etcd_key = self._http_middleware_etcd_key(
            ingress.authority, self._auth_plugin_middleware_name(ingress_key)
        )
        middleware_configs[auth_plugin_etcd_key] = self._auth_plugin_middleware_config(ingress)
        return middleware_configs

    def _ip_allowlist_middleware_config(
        self, access: IngressAccess
    ) -> TraefikIpAllowListMiddlewareConfig:
        ip_allowlist: TraefikIpAllowList = {
            "sourceRange": [str(network) for network in access.allowed_client_ips],
        }
        client_ip_strategy = self._traefik_config.client_ip_strategy
        if client_ip_strategy is not None:
            if client_ip_strategy.depth is not None:
                ip_allowlist["ipStrategy"] = {"depth": client_ip_strategy.depth}
            elif client_ip_strategy.excluded_ips:
                ip_allowlist["ipStrategy"] = {
                    "excludedIPs": [str(network) for network in client_ip_strategy.excluded_ips],
                }
        return {"ipAllowList": ip_allowlist}

    def _auth_plugin_middleware_config(self, ingress: Ingress) -> TraefikAuthPluginMiddlewareConfig:
        return {
            "plugin": {
                "appproxy-traefik-plugin": {
                    # etcd holds strings only, so the ingress travels as one JSON value.
                    "ingress": ingress.model_dump_json(),
                    "jwt_secret": self._secrets.jwt_secret,
                    "permit_hash_secret": self._permit_hash.secret.decode(),
                    "permit_cookie_name": PERMIT_COOKIE_NAME,
                },
            },
        }

    @classmethod
    def _http_service_config(cls, backend: IngressBackend) -> TraefikHttpServiceConfig:
        servers: list[TraefikHttpServer] = [
            {"url": f"http://{target.host}:{target.port}/"}
            for target in cls._targets_receiving_traffic(backend)
        ]
        if not servers:
            return {}
        return {"loadBalancer": {"servers": servers}}

    @classmethod
    def _tcp_service_config(cls, backend: IngressBackend) -> TraefikTcpServiceConfig:
        servers: list[TraefikTcpServer] = [
            {"address": f"{target.host}:{target.port}"}
            for target in cls._targets_receiving_traffic(backend)
        ]
        if not servers:
            return {}
        return {"loadBalancer": {"servers": servers}}

    # Frontend keys hold no '_', so no router, service or middleware name of one ingress is a
    # prefix of another's.
    @staticmethod
    def _router_name(ingress_key: IngressKey) -> str:
        return f"bai_ingress_{ingress_key.frontend_key}_router"

    @staticmethod
    def _service_name(ingress_key: IngressKey) -> str:
        return f"bai_ingress_{ingress_key.frontend_key}_service"

    @staticmethod
    def _ip_allowlist_middleware_name(ingress_key: IngressKey) -> str:
        return f"bai_ingress_{ingress_key.frontend_key}_ipallowlist"

    @staticmethod
    def _auth_plugin_middleware_name(ingress_key: IngressKey) -> str:
        return f"bai_ingress_{ingress_key.frontend_key}_auth"

    @staticmethod
    def _traefik_protocol_key(protocol: IngressProtocol) -> str:
        # Traefik keeps HTTP/2 routing under its http configuration.
        match protocol:
            case IngressProtocol.HTTP | IngressProtocol.HTTP2:
                return "http"
            case IngressProtocol.TCP:
                return "tcp"

    @staticmethod
    def _http_middleware_etcd_key(authority: IngressAuthority, middleware_name: str) -> str:
        return f"worker_{authority}/http/middlewares/{middleware_name}"

    @staticmethod
    def _host_rule(ingress: Ingress, *, hostname: str, wildcard_domain: str | None) -> str:
        match ingress.frontend.kind:
            case IngressFrontendKind.PORT:
                return f"Host(`{hostname}`)"
            case IngressFrontendKind.WILDCARD:
                if wildcard_domain is None:
                    raise TraefikWildcardDomainMissingError(
                        extra_data={"authority": ingress.authority}
                    )
                return f"Host(`{ingress.frontend.key()}{wildcard_domain}`)"

    @staticmethod
    def _client_ip_rule(access: IngressAccess) -> str:
        allowed_client_ip_ranges = [str(network) for network in access.allowed_client_ips]
        if not allowed_client_ip_ranges:
            return "ClientIP(`0.0.0.0/0`)"
        # Traefik v3 rule matchers take one value each, so the ranges are joined with ||.
        return " || ".join(f"ClientIP(`{cidr}`)" for cidr in allowed_client_ip_ranges)

    @staticmethod
    def _entrypoint_name(frontend: IngressFrontend) -> str:
        match frontend.kind:
            case IngressFrontendKind.PORT:
                return f"portproxy_{frontend.key()}"
            case IngressFrontendKind.WILDCARD:
                return "domainproxy"

    @staticmethod
    def _targets_receiving_traffic(backend: IngressBackend) -> list[IngressTarget]:
        return [
            target
            for group in backend.target_groups
            if group.weight > 0
            for target in group.targets
        ]
