from __future__ import annotations

from dataclasses import dataclass

from ai.backend.appproxy.common.config import PermitHashConfig, SecretConfig
from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.common.etcd import convert_to_etcd_dict
from ai.backend.appproxy.common.types import WorkerFrontend
from ai.backend.appproxy.coordinator.clients.worker.traefik.types import (
    AuthPluginMiddlewareConfig,
    CorsHeadersMiddlewareConfig,
    HttpRouterConfig,
    HttpServer,
    HttpServiceConfig,
    IngressRoutingConfigs,
    IpAllowList,
    IpAllowListMiddlewareConfig,
    TcpRouterConfig,
    TcpServer,
    TcpServiceConfig,
)
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
    PortFrontend,
    WildcardFrontend,
)
from ai.backend.common.etcd import NestedStrKeyedMapping
from ai.backend.common.exception import UnreachableError


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

    def build_routing_configs(
        self, ingress: Ingress, worker_frontend: WorkerFrontend
    ) -> IngressRoutingConfigs:
        match ingress.frontend.protocol:
            case IngressProtocol.TCP:
                return IngressRoutingConfigs(
                    tcp_router=self._tcp_router_config(ingress),
                    tcp_service=self._tcp_service_config(ingress.backend),
                )
            case IngressProtocol.HTTP | IngressProtocol.HTTP2:
                return IngressRoutingConfigs(
                    http_router=self._http_router_config(
                        ingress,
                        host_rule=self._host_rule(
                            ingress,
                            hostname=worker_frontend.hostname,
                            wildcard_domain=worker_frontend.wildcard_domain,
                        ),
                        tls_listen=worker_frontend.tls_listen,
                    ),
                    http_service=self._http_service_config(ingress.backend),
                    cors_headers_middleware=self._cors_headers_middleware_config(),
                    ip_allowlist_middleware=(
                        self._ip_allowlist_middleware_config(ingress.access)
                        if ingress.access.allowed_client_ips
                        else None
                    ),
                    auth_plugin_middleware=self._auth_plugin_middleware_config(ingress),
                )

    @classmethod
    def build_etcd_subtrees(
        cls, ingress_key: IngressKey, routing_configs: IngressRoutingConfigs
    ) -> dict[str, NestedStrKeyedMapping]:
        """Clears every config the ingress does not have."""
        authority = ingress_key.authority
        subtrees_by_etcd_prefix: dict[str, NestedStrKeyedMapping] = {
            cls._router_etcd_key(ingress_key, IngressProtocol.HTTP): convert_to_etcd_dict(
                routing_configs.http_router or {}
            ),
            cls._service_etcd_key(ingress_key, IngressProtocol.HTTP): convert_to_etcd_dict(
                routing_configs.http_service or {}
            ),
            cls._http_middleware_etcd_key(
                authority, cls._cors_headers_middleware_name(ingress_key)
            ): convert_to_etcd_dict(routing_configs.cors_headers_middleware or {}),
            cls._http_middleware_etcd_key(
                authority, cls._ip_allowlist_middleware_name(ingress_key)
            ): convert_to_etcd_dict(routing_configs.ip_allowlist_middleware or {}),
            cls._http_middleware_etcd_key(
                authority, cls._auth_plugin_middleware_name(ingress_key)
            ): convert_to_etcd_dict(routing_configs.auth_plugin_middleware or {}),
            cls._router_etcd_key(ingress_key, IngressProtocol.TCP): convert_to_etcd_dict(
                routing_configs.tcp_router or {}
            ),
            cls._service_etcd_key(ingress_key, IngressProtocol.TCP): convert_to_etcd_dict(
                routing_configs.tcp_service or {}
            ),
        }
        return subtrees_by_etcd_prefix

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
    ) -> HttpRouterConfig:
        ingress_key = ingress.key()
        # The ipAllowList middleware must precede the auth plugin so that disallowed
        # clients are rejected before any credential handling.
        middleware_names = [cls._cors_headers_middleware_name(ingress_key)]
        if ingress.access.allowed_client_ips:
            middleware_names.append(cls._ip_allowlist_middleware_name(ingress_key))
        middleware_names.append(cls._auth_plugin_middleware_name(ingress_key))
        router_config: HttpRouterConfig = {
            "rule": host_rule,
            "service": cls._service_name(ingress_key),
            "entrypoints": [cls._entrypoint_name(ingress.frontend)],
            "middlewares": middleware_names,
        }
        if tls_listen:
            router_config["tls"] = "true"
        return router_config

    @classmethod
    def _tcp_router_config(cls, ingress: Ingress) -> TcpRouterConfig:
        return {
            "rule": cls._client_ip_rule(ingress.access),
            "service": cls._service_name(ingress.key()),
            "entrypoints": [cls._entrypoint_name(ingress.frontend)],
        }

    @staticmethod
    def _cors_headers_middleware_config() -> CorsHeadersMiddlewareConfig:
        return {
            "headers": {
                "accessControlAllowHeaders": "*",
                "accessControlAllowOriginList": ["*"],
            },
        }

    def _ip_allowlist_middleware_config(self, access: IngressAccess) -> IpAllowListMiddlewareConfig:
        ip_allowlist: IpAllowList = {
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

    def _auth_plugin_middleware_config(self, ingress: Ingress) -> AuthPluginMiddlewareConfig:
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
    def _http_service_config(cls, backend: IngressBackend) -> HttpServiceConfig:
        servers: list[HttpServer] = [
            {"url": f"http://{target.host}:{target.port}/"}
            for target in cls._targets_receiving_traffic(backend)
        ]
        if not servers:
            return {}
        return {"loadBalancer": {"servers": servers}}

    @classmethod
    def _tcp_service_config(cls, backend: IngressBackend) -> TcpServiceConfig:
        servers: list[TcpServer] = [
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
    def _cors_headers_middleware_name(ingress_key: IngressKey) -> str:
        return f"bai_ingress_{ingress_key.frontend_key}_cors"

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
        match ingress.frontend:
            case IngressFrontend(kind=IngressFrontendKind.PORT):
                return f"Host(`{hostname}`)"
            case IngressFrontend(
                kind=IngressFrontendKind.WILDCARD, wildcard=WildcardFrontend(subdomain=subdomain)
            ):
                if wildcard_domain is None:
                    raise TraefikWildcardDomainMissingError(
                        extra_data={"authority": ingress.authority}
                    )
                return f"Host(`{subdomain}{wildcard_domain}`)"
            case _:
                raise UnreachableError("A validated wildcard frontend sets wildcard")

    @staticmethod
    def _client_ip_rule(access: IngressAccess) -> str:
        allowed_client_ip_ranges = [str(network) for network in access.allowed_client_ips]
        if not allowed_client_ip_ranges:
            return "ClientIP(`0.0.0.0/0`)"
        # Traefik v3 rule matchers take one value each, so the ranges are joined with ||.
        return " || ".join(f"ClientIP(`{cidr}`)" for cidr in allowed_client_ip_ranges)

    @staticmethod
    def _entrypoint_name(frontend: IngressFrontend) -> str:
        match frontend:
            case IngressFrontend(
                kind=IngressFrontendKind.PORT, port=PortFrontend(number=port_number)
            ):
                return f"portproxy_{port_number}"
            case IngressFrontend(kind=IngressFrontendKind.WILDCARD):
                return "domainproxy"
            case _:
                raise UnreachableError("A validated port frontend sets port")

    @staticmethod
    def _targets_receiving_traffic(backend: IngressBackend) -> list[IngressTarget]:
        return [
            target
            for group in backend.target_groups
            if group.weight > 0
            for target in group.targets
        ]
