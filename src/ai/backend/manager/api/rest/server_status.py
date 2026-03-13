"""Server-status route middleware (DI-based).

Provides ``server_status_required`` which checks the current manager status
before allowing a request through.  Receives ``config_provider`` via
constructor dependency injection.

Constants ``READ_ALLOWED`` and ``ALL_ALLOWED`` define the standard
status sets used across all REST registry modules.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Final

from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api.utils import set_handler_attr
from ai.backend.manager.errors.common import ServerFrozen, ServiceUnavailable

from .types import RouteMiddleware

if TYPE_CHECKING:
    from ai.backend.manager.config.provider import ManagerConfigProvider

READ_ALLOWED: Final[frozenset[ManagerStatus]] = frozenset({
    ManagerStatus.RUNNING,
    ManagerStatus.FROZEN,
})

ALL_ALLOWED: Final[frozenset[ManagerStatus]] = frozenset({ManagerStatus.RUNNING})


def server_status_required(
    allowed_status: frozenset[ManagerStatus],
    config_provider: ManagerConfigProvider,
) -> RouteMiddleware:
    """Route middleware that rejects requests when the manager is not in *allowed_status*.

    Raises ``ServerFrozen`` when the manager is frozen and ``ServiceUnavailable``
    for any other disallowed status.

    Handler attributes ``server_status_required`` and ``required_server_statuses``
    are set on the wrapped handler for OpenAPI documentation generation.
    """

    def decorator(handler: Handler) -> Handler:
        @functools.wraps(handler)
        async def wrapped(request: web.Request, *args: Any, **kwargs: Any) -> web.StreamResponse:
            status = await config_provider.legacy_etcd_config_loader.get_manager_status()
            if status not in allowed_status:
                if status == ManagerStatus.FROZEN:
                    raise ServerFrozen
                msg = f"Server is not in the required status: {allowed_status}"
                raise ServiceUnavailable(msg)
            return await handler(request, *args, **kwargs)

        set_handler_attr(wrapped, "server_status_required", True)
        set_handler_attr(wrapped, "required_server_statuses", allowed_status)

        return wrapped

    return decorator
