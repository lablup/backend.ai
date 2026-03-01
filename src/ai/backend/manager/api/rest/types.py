from __future__ import annotations

import dataclasses
from collections.abc import Awaitable, Callable, Iterable, Mapping
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.common.api_handlers import APIResponse, APIStreamResponse

if TYPE_CHECKING:
    from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
    from ai.backend.manager.config.unified import AuthConfig
    from ai.backend.manager.service.base import ServicesContext
    from ai.backend.manager.services.processors import Processors

    from .routing import RouteRegistry

type WebRequestHandler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
type WebMiddleware = Middleware

type CORSOptions = Mapping[str, aiohttp_cors.ResourceOptions]
type AppCreator = Callable[
    [CORSOptions],
    tuple[web.Application, Iterable[WebMiddleware]],
]

type RouteMiddleware = Callable[
    [WebRequestHandler],
    WebRequestHandler,
]

type ApiHandler = Callable[..., Awaitable[APIResponse | APIStreamResponse | web.StreamResponse]]


@dataclasses.dataclass(frozen=True, slots=True)
class ModuleDeps:
    """Shared dependencies injected into all API module registrar functions."""

    cors_options: CORSOptions
    processors: Processors | None = None
    services_ctx: ServicesContext | None = None
    storage_manager: StorageSessionManager | None = None
    auth_config: AuthConfig | None = None


type ModuleRegistrar = Callable[[ModuleDeps], RouteRegistry]
