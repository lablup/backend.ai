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
    IngressProtocol,
    IngressTarget,
)


class TraefikRoutingConfigFactory:
    """Builds the Traefik router, middleware and service configs of an ingress.
    Object names stay with the caller."""

    CORS_HEADERS_MIDDLEWARE_NAME: Final[str] = "CORSHeaders"

    _client_ip_strategy: ClientIPStrategyConfig | None
    _jwt_secret: str
    _permit_hash_secret: str

    def __init__(
        self, traefik_config: TraefikConfig, *, jwt_secret: str, permit_hash_secret: str
    ) -> None:
        self._client_ip_strategy = traefik_config.client_ip_strategy
        self._jwt_secret = jwt_secret
        self._permit_hash_secret = permit_hash_secret

    @staticmethod
    def etcd_prefix(authority: IngressAuthority, protocol: IngressProtocol) -> str:
        match protocol:
            case IngressProtocol.HTTP | IngressProtocol.HTTP2:
                return f"worker_{authority}/http"
            case IngressProtocol.TCP:
                return f"worker_{authority}/tcp"

    @staticmethod
    def router_rule(ingress: Ingress, worker: TraefikWorker) -> str:
        frontend = ingress.frontend
        match frontend.protocol:
            case IngressProtocol.TCP:
                ranges = [str(network) for network in ingress.access.allowed_client_ips]
                if not ranges:
                    return "ClientIP(`0.0.0.0/0`)"
                return "ClientIP(" + ", ".join(f"`{cidr}`" for cidr in ranges) + ")"
            case IngressProtocol.HTTP | IngressProtocol.HTTP2:
                match frontend.kind:
                    case IngressFrontendKind.PORT:
                        return f"Host(`{worker.hostname}`)"
                    case IngressFrontendKind.WILDCARD:
                        if worker.wildcard_domain is None:
                            raise TraefikWildcardDomainMissingError(
                                extra_data={"authority": ingress.authority}
                            )
                        return f"Host(`{frontend.key()}{worker.wildcard_domain}`)"

    @staticmethod
    def entrypoint_name(frontend: IngressFrontend) -> str:
        match frontend.kind:
            case IngressFrontendKind.PORT:
                return f"portproxy_{frontend.key()}"
            case IngressFrontendKind.WILDCARD:
                return "domainproxy"

    @classmethod
    def http_router_config(
        cls,
        rule: str,
        service_name: str,
        entrypoint_name: str,
        *,
        ip_allowlist_middleware_name: str | None,
        auth_plugin_middleware_name: str,
        tls: bool,
    ) -> dict[str, Any]:
        # The ipAllowList middleware must precede the auth plugin so that disallowed
        # clients are rejected before any credential handling.
        middlewares = [cls.CORS_HEADERS_MIDDLEWARE_NAME]
        if ip_allowlist_middleware_name is not None:
            middlewares.append(ip_allowlist_middleware_name)
        middlewares.append(auth_plugin_middleware_name)
        router: dict[str, Any] = {
            "rule": rule,
            "service": service_name,
            "entrypoints": [entrypoint_name],
            "middlewares": middlewares,
        }
        if tls:
            router["tls"] = ""
        return router

    @staticmethod
    def tcp_router_config(rule: str, service_name: str, entrypoint_name: str) -> dict[str, Any]:
        return {"rule": rule, "service": service_name, "entrypoints": [entrypoint_name]}

    @staticmethod
    def cors_headers_middleware_config() -> dict[str, Any]:
        return {
            "headers": {
                "accessControlAllowHeaders": "*",
                "accessControlAllowOriginList": ["*"],
            },
        }

    def ip_allowlist_middleware_config(self, access: IngressAccess) -> dict[str, Any]:
        ip_allowlist: dict[str, Any] = {
            "sourceRange": [str(network) for network in access.allowed_client_ips],
        }
        strategy = self._client_ip_strategy
        if strategy is not None:
            if strategy.depth is not None:
                ip_allowlist["ipStrategy"] = {"depth": strategy.depth}
            elif strategy.excluded_ips:
                ip_allowlist["ipStrategy"] = {
                    "excludedIPs": [str(network) for network in strategy.excluded_ips],
                }
        return {"ipAllowList": ip_allowlist}

    def auth_plugin_middleware_config(self, ingress: Ingress) -> dict[str, Any]:
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


def _targets_receiving_traffic(backend: IngressBackend) -> list[IngressTarget]:
    return [
        target for group in backend.target_groups if group.weight > 0 for target in group.targets
    ]
