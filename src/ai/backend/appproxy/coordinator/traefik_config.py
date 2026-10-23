from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.coordinator.config import ClientIPStrategyConfig, TraefikConfig


class TraefikConfigBuilder:
    """Builds the Traefik router, middleware and service configs that circuits and ingresses share.
    Object names stay with each caller."""

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
    def host_rule(host: str) -> str:
        return f"Host(`{host}`)"

    @staticmethod
    def client_ip_rule(ranges: Sequence[str]) -> str:
        # TCP routers take no middlewares, so the allowlist goes into the match rule.
        if not ranges:
            return "ClientIP(`0.0.0.0/0`)"
        return "ClientIP(" + ", ".join(f"`{cidr}`" for cidr in ranges) + ")"

    @staticmethod
    def port_entrypoint_name(port: int) -> str:
        return f"portproxy_{port}"

    @staticmethod
    def domain_entrypoint_name() -> str:
        return "domainproxy"

    @staticmethod
    def http_router_config(
        rule: str, service: str, entrypoint: str, middlewares: Sequence[str], *, tls: bool
    ) -> dict[str, Any]:
        router: dict[str, Any] = {
            "rule": rule,
            "service": service,
            "entrypoints": [entrypoint],
            "middlewares": list(middlewares),
        }
        if tls:
            router["tls"] = ""
        return router

    @staticmethod
    def tcp_router_config(rule: str, service: str, entrypoint: str) -> dict[str, Any]:
        return {"rule": rule, "service": service, "entrypoints": [entrypoint]}

    @staticmethod
    def cors_headers_middleware_config() -> dict[str, Any]:
        return {
            "headers": {
                "accessControlAllowHeaders": "*",
                "accessControlAllowOriginList": ["*"],
            },
        }

    def ip_allowlist_middleware_config(self, ranges: Sequence[str]) -> dict[str, Any]:
        # Without a strategy Traefik matches the direct connection address; behind a load
        # balancer the strategy makes it read the client address from X-Forwarded-For.
        ip_allowlist: dict[str, Any] = {"sourceRange": list(ranges)}
        strategy = self._client_ip_strategy
        if strategy is not None:
            if strategy.depth is not None:
                ip_allowlist["ipStrategy"] = {"depth": strategy.depth}
            elif strategy.excluded_ips:
                ip_allowlist["ipStrategy"] = {
                    "excludedIPs": [str(network) for network in strategy.excluded_ips],
                }
        return {"ipAllowList": ip_allowlist}

    def auth_plugin_middleware_config(self, payload_name: str, payload_json: str) -> dict[str, Any]:
        return {
            "plugin": {
                "appproxy-traefik-plugin": {
                    # etcd holds strings only, so the payload travels as one JSON value.
                    payload_name: payload_json,
                    "jwt_secret": self._jwt_secret,
                    "permit_hash_secret": self._permit_hash_secret,
                    "permit_cookie_name": PERMIT_COOKIE_NAME,
                },
            },
        }

    @staticmethod
    def http_service_config(
        servers: Sequence[tuple[str, int]], health_check: Mapping[str, str] | None = None
    ) -> dict[str, Any]:
        if not servers:
            return {}
        load_balancer: dict[str, Any] = {
            "servers": [{"url": f"http://{host}:{port}/"} for host, port in servers],
        }
        if health_check is not None:
            load_balancer["healthCheck"] = dict(health_check)
        return {"loadBalancer": load_balancer}

    @staticmethod
    def tcp_service_config(servers: Sequence[tuple[str, int]]) -> dict[str, Any]:
        if not servers:
            return {}
        return {
            "loadBalancer": {
                "servers": [{"address": f"{host}:{port}"} for host, port in servers],
            },
        }
