from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypedDict, override

from pydantic import ConfigDict

from ai.backend.appproxy.coordinator.errors.ingress import TraefikAppliedIngressRevisionInvalidError
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import BackendAISchema, SchemaValidationFailureInfo


class HttpRouterConfig(TypedDict):
    rule: str
    service: str
    entrypoints: list[str]
    middlewares: list[str]
    tls: NotRequired[str]


class TcpRouterConfig(TypedDict):
    rule: str
    service: str
    entrypoints: list[str]


class HttpServer(TypedDict):
    url: str


class HttpLoadBalancer(TypedDict):
    servers: list[HttpServer]


class HttpServiceConfig(TypedDict):
    # Left out when no target receives traffic, which clears the service.
    loadBalancer: NotRequired[HttpLoadBalancer]


class TcpServer(TypedDict):
    address: str


class TcpLoadBalancer(TypedDict):
    servers: list[TcpServer]


class TcpServiceConfig(TypedDict):
    # Left out when no target receives traffic, which clears the service.
    loadBalancer: NotRequired[TcpLoadBalancer]


class CorsHeaders(TypedDict):
    accessControlAllowHeaders: str
    accessControlAllowOriginList: list[str]


class CorsHeadersMiddlewareConfig(TypedDict):
    headers: CorsHeaders


class IpStrategy(TypedDict, total=False):
    depth: int
    excludedIPs: list[str]


class IpAllowList(TypedDict):
    sourceRange: list[str]
    ipStrategy: NotRequired[IpStrategy]


class IpAllowListMiddlewareConfig(TypedDict):
    ipAllowList: IpAllowList


class AuthPluginOptions(TypedDict):
    ingress: str
    jwt_secret: str
    permit_hash_secret: str
    permit_cookie_name: str


AuthPluginOptionsByName = TypedDict(
    "AuthPluginOptionsByName", {"appproxy-traefik-plugin": AuthPluginOptions}
)


class AuthPluginMiddlewareConfig(TypedDict):
    plugin: AuthPluginOptionsByName


@dataclass(frozen=True)
class IngressRoutingConfigs:
    http_router: HttpRouterConfig | None = None
    http_service: HttpServiceConfig | None = None
    cors_headers_middleware: CorsHeadersMiddlewareConfig | None = None
    ip_allowlist_middleware: IpAllowListMiddlewareConfig | None = None
    auth_plugin_middleware: AuthPluginMiddlewareConfig | None = None
    tcp_router: TcpRouterConfig | None = None
    tcp_service: TcpServiceConfig | None = None


class AppliedIngressRevision(BackendAISchema):
    model_config = ConfigDict(frozen=True)

    revision: int

    @override
    @classmethod
    def build_validation_error(cls, info: SchemaValidationFailureInfo) -> BackendAIError:
        return TraefikAppliedIngressRevisionInvalidError(
            extra_msg=info.summary, extra_data={"errors": info.errors}
        )
