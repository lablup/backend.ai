from __future__ import annotations

from typing import Any, Final

from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.coordinator.config import ClientIPStrategyConfig, TraefikConfig
from ai.backend.appproxy.coordinator.errors.ingress import TraefikWildcardDomainMissingError
from ai.backend.appproxy.coordinator.repositories.worker import TraefikWorker
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


class TraefikRoutingConfigFactory:
    """Builds the Traefik router, middleware and service configs of an ingress and the etcd keys
    Traefik reads them from."""

    _client_ip_strategy: ClientIPStrategyConfig | None
    _jwt_secret: str
    _permit_hash_secret: str

    def __init__(
        self, traefik_config: TraefikConfig, *, jwt_secret: str, permit_hash_secret: str
    ) -> None:
        self._client_ip_strategy = traefik_config.client_ip_strategy
        self._jwt_secret = jwt_secret
        self._permit_hash_secret = permit_hash_secret

    @classmethod
    def object_etcd_keys(cls, ingress_key: IngressKey) -> list[str]:
        """Every object key an ingress can own, for clearing the ones it no longer has."""
        return [
            cls.router_etcd_key(ingress_key, IngressProtocol.HTTP),
            cls.service_etcd_key(ingress_key, IngressProtocol.HTTP),
            _http_middleware_etcd_key(
                ingress_key.authority, _ip_allowlist_middleware_name(ingress_key)
            ),
            _http_middleware_etcd_key(
                ingress_key.authority, _auth_plugin_middleware_name(ingress_key)
            ),
            cls.router_etcd_key(ingress_key, IngressProtocol.TCP),
            cls.service_etcd_key(ingress_key, IngressProtocol.TCP),
        ]

    @staticmethod
    def router_etcd_key(ingress_key: IngressKey, protocol: IngressProtocol) -> str:
        traefik_protocol_key = _traefik_protocol_key(protocol)
        return (
            f"worker_{ingress_key.authority}/{traefik_protocol_key}/routers/"
            f"{_router_name(ingress_key)}"
        )

    @staticmethod
    def service_etcd_key(ingress_key: IngressKey, protocol: IngressProtocol) -> str:
        traefik_protocol_key = _traefik_protocol_key(protocol)
        return (
            f"worker_{ingress_key.authority}/{traefik_protocol_key}/services/"
            f"{_service_name(ingress_key)}"
        )

    @staticmethod
    def http_router_config(ingress: Ingress, worker: TraefikWorker) -> dict[str, Any]:
        ingress_key = ingress.key()
        # The ipAllowList middleware must precede the auth plugin so that disallowed
        # clients are rejected before any credential handling.
        middleware_names = [_CORS_HEADERS_MIDDLEWARE_NAME]
        if ingress.access.allowed_client_ips:
            middleware_names.append(_ip_allowlist_middleware_name(ingress_key))
        middleware_names.append(_auth_plugin_middleware_name(ingress_key))
        router_config: dict[str, Any] = {
            "rule": _host_rule(ingress, worker),
            "service": _service_name(ingress_key),
            "entrypoints": [_entrypoint_name(ingress.frontend)],
            "middlewares": middleware_names,
        }
        if worker.tls_listen:
            router_config["tls"] = ""
        return router_config

    @staticmethod
    def tcp_router_config(ingress: Ingress) -> dict[str, Any]:
        return {
            "rule": _client_ip_rule(ingress.access),
            "service": _service_name(ingress.key()),
            "entrypoints": [_entrypoint_name(ingress.frontend)],
        }

    def http_middleware_configs(self, ingress: Ingress) -> dict[str, dict[str, Any]]:
        """The configs of the middlewares the HTTP router of the ingress uses, by etcd key."""
        ingress_key = ingress.key()
        middleware_configs: dict[str, dict[str, Any]] = {
            _http_middleware_etcd_key(ingress.authority, _CORS_HEADERS_MIDDLEWARE_NAME): {
                "headers": {
                    "accessControlAllowHeaders": "*",
                    "accessControlAllowOriginList": ["*"],
                },
            },
        }
        if ingress.access.allowed_client_ips:
            ip_allowlist_etcd_key = _http_middleware_etcd_key(
                ingress.authority, _ip_allowlist_middleware_name(ingress_key)
            )
            middleware_configs[ip_allowlist_etcd_key] = self._ip_allowlist_middleware_config(
                ingress.access
            )
        auth_plugin_etcd_key = _http_middleware_etcd_key(
            ingress.authority, _auth_plugin_middleware_name(ingress_key)
        )
        middleware_configs[auth_plugin_etcd_key] = self._auth_plugin_middleware_config(ingress)
        return middleware_configs

    @staticmethod
    def http_service_config(backend: IngressBackend) -> dict[str, Any]:
        servers = [
            {"url": f"http://{target.host}:{target.port}/"}
            for target in _targets_receiving_traffic(backend)
        ]
        if not servers:
            return {}
        return {"loadBalancer": {"servers": servers}}

    @staticmethod
    def tcp_service_config(backend: IngressBackend) -> dict[str, Any]:
        servers = [
            {"address": f"{target.host}:{target.port}"}
            for target in _targets_receiving_traffic(backend)
        ]
        if not servers:
            return {}
        return {"loadBalancer": {"servers": servers}}

    def _ip_allowlist_middleware_config(self, access: IngressAccess) -> dict[str, Any]:
        ip_allowlist: dict[str, Any] = {
            "sourceRange": [str(network) for network in access.allowed_client_ips],
        }
        client_ip_strategy = self._client_ip_strategy
        if client_ip_strategy is not None:
            if client_ip_strategy.depth is not None:
                ip_allowlist["ipStrategy"] = {"depth": client_ip_strategy.depth}
            elif client_ip_strategy.excluded_ips:
                ip_allowlist["ipStrategy"] = {
                    "excludedIPs": [str(network) for network in client_ip_strategy.excluded_ips],
                }
        return {"ipAllowList": ip_allowlist}

    def _auth_plugin_middleware_config(self, ingress: Ingress) -> dict[str, Any]:
        return {
            "plugin": {
                "appproxy-traefik-plugin": {
                    # etcd holds strings only, so the ingress travels as one JSON value.
                    "ingress": ingress.model_dump_json(),
                    "jwt_secret": self._jwt_secret,
                    "permit_hash_secret": self._permit_hash_secret,
                    "permit_cookie_name": PERMIT_COOKIE_NAME,
                },
            },
        }


# Frontend keys hold no '_', so no object name of one ingress is a prefix of another's.
def _router_name(ingress_key: IngressKey) -> str:
    return f"bai_ingress_{ingress_key.frontend_key}_router"


def _service_name(ingress_key: IngressKey) -> str:
    return f"bai_ingress_{ingress_key.frontend_key}_service"


def _ip_allowlist_middleware_name(ingress_key: IngressKey) -> str:
    return f"bai_ingress_{ingress_key.frontend_key}_ipallowlist"


def _auth_plugin_middleware_name(ingress_key: IngressKey) -> str:
    return f"bai_ingress_{ingress_key.frontend_key}_auth"


def _traefik_protocol_key(protocol: IngressProtocol) -> str:
    # Traefik keeps HTTP/2 routing under its http configuration.
    match protocol:
        case IngressProtocol.HTTP | IngressProtocol.HTTP2:
            return "http"
        case IngressProtocol.TCP:
            return "tcp"


def _http_middleware_etcd_key(authority: IngressAuthority, middleware_name: str) -> str:
    return f"worker_{authority}/http/middlewares/{middleware_name}"


def _host_rule(ingress: Ingress, worker: TraefikWorker) -> str:
    match ingress.frontend.kind:
        case IngressFrontendKind.PORT:
            return f"Host(`{worker.hostname}`)"
        case IngressFrontendKind.WILDCARD:
            if worker.wildcard_domain is None:
                raise TraefikWildcardDomainMissingError(extra_data={"authority": ingress.authority})
            return f"Host(`{ingress.frontend.key()}{worker.wildcard_domain}`)"


def _client_ip_rule(access: IngressAccess) -> str:
    allowed_client_ip_ranges = [str(network) for network in access.allowed_client_ips]
    if not allowed_client_ip_ranges:
        return "ClientIP(`0.0.0.0/0`)"
    return "ClientIP(" + ", ".join(f"`{cidr}`" for cidr in allowed_client_ip_ranges) + ")"


def _entrypoint_name(frontend: IngressFrontend) -> str:
    match frontend.kind:
        case IngressFrontendKind.PORT:
            return f"portproxy_{frontend.key()}"
        case IngressFrontendKind.WILDCARD:
            return "domainproxy"


def _targets_receiving_traffic(backend: IngressBackend) -> list[IngressTarget]:
    return [
        target for group in backend.target_groups if group.weight > 0 for target in group.targets
    ]
