import asyncio
import weakref
from dataclasses import dataclass, field
from typing import TypeAlias

from aiohttp import web

WeakTaskSet: TypeAlias = weakref.WeakSet[asyncio.Task]


@dataclass
class WebStats:
    active_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_static_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_webui_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_config_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_login_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_login_check_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_token_login_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_logout_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_healthcheck_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_proxy_api_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_proxy_plugin_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())
    active_proxy_websocket_handlers: WeakTaskSet = field(default_factory=lambda: weakref.WeakSet())


@web.middleware
async def track_active_handlers(request: web.Request, handler) -> web.StreamResponse:
    stats: WebStats = request.app["stats"]
    stats.active_handlers.add(asyncio.current_task())  # type: ignore
    return await handler(request)


async def view_stats(request: web.Request) -> web.Response:
    stats: WebStats = request.app["stats"]
    match request.query.get("format", "text"):
        case "text":
            text = "\n".join([
                f"total_async_tasks: {len(asyncio.all_tasks())}",
                f"total_active_handlers: {len(stats.active_handlers)}",
                f"active_static_handlers: {len(stats.active_static_handlers)}",
                f"active_webui_handlers: {len(stats.active_webui_handlers)}",
                f"active_config_handlers: {len(stats.active_config_handlers)}",
                f"active_login_handlers: {len(stats.active_login_handlers)}",
                f"active_login_check_handlers: {len(stats.active_login_check_handlers)}",
                f"active_token_login_handlers: {len(stats.active_token_login_handlers)}",
                f"active_logout_handlers: {len(stats.active_logout_handlers)}",
                f"active_healthcheck_handlers: {len(stats.active_healthcheck_handlers)}",
                f"active_proxy_api_handlers: {len(stats.active_proxy_api_handlers)}",
                f"active_proxy_plugin_handlers: {len(stats.active_proxy_plugin_handlers)}",
                f"active_proxy_websocket_handlers: {len(stats.active_proxy_websocket_handlers)}",
            ])
            return web.Response(text=text)
        case "json":
            data = {
                "total_async_tasks": len(asyncio.all_tasks()),
                "total_active_handlers": len(stats.active_handlers),
                "active_static_handlers": len(stats.active_static_handlers),
                "active_webui_handlers": len(stats.active_webui_handlers),
                "active_config_handlers": len(stats.active_config_handlers),
                "active_login_handlers": len(stats.active_login_handlers),
                "active_login_check_handlers": len(stats.active_login_check_handlers),
                "active_token_login_handlers": len(stats.active_token_login_handlers),
                "active_logout_handlers": len(stats.active_logout_handlers),
                "active_healthcheck_handlers": len(stats.active_healthcheck_handlers),
                "active_proxy_api_handlers": len(stats.active_proxy_api_handlers),
                "active_proxy_plugin_handlers": len(stats.active_proxy_plugin_handlers),
                "active_proxy_websocket_handlers": len(stats.active_proxy_websocket_handlers),
            }
            return web.json_response(data)
        case _ as invalid_format:
            raise web.HTTPBadRequest(text=f"Invalid format: {invalid_format}")
