from __future__ import annotations

from typing import NotRequired, TypedDict


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


type HttpMiddlewareConfig = (
    CorsHeadersMiddlewareConfig | IpAllowListMiddlewareConfig | AuthPluginMiddlewareConfig
)
type RoutingConfig = (
    HttpRouterConfig | TcpRouterConfig | HttpServiceConfig | TcpServiceConfig | HttpMiddlewareConfig
)
