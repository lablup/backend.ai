from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterable, Tuple

import aiohttp_cors
import attrs
from aiohttp import web
from strawberry.aiohttp.views import GraphQLView

from ai.backend.logging import BraceStyleAdapter

from ..auth import auth_required
from ..types import CORSOptions, WebMiddleware
from .schema import schema

if TYPE_CHECKING:
    from ..context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StrawberryGraphQLView(GraphQLView):
    async def get_context(self, request: web.Request, response: web.Response) -> Any:
        """Create context for Strawberry GraphQL execution"""
        root_ctx: RootContext = request.app["_root.context"]

        # Create context similar to existing Graphene implementation
        # but simplified for Strawberry
        context = {
            "request": request,
            "response": response,
            "user": request.get("user"),
            "access_key": request.get("keypair", {}).get("access_key"),
            "config_provider": root_ctx.config_provider,
            "etcd": root_ctx.etcd,
            "db": root_ctx.db,
            "storage_manager": root_ctx.storage_manager,
            "registry": root_ctx.registry,
        }

        return context

    async def handle_request(self, request: web.Request) -> web.Response:
        """Handle GraphQL requests - compatibility method"""
        return await super().__call__(request)


@attrs.define(auto_attribs=True, slots=True, init=False)
class StrawberryContext:
    """Context for Strawberry GraphQL app"""

    schema: Any


async def init(app: web.Application) -> None:
    """Initialize Strawberry GraphQL app"""
    app_ctx: StrawberryContext = app["gql.context"]
    app_ctx.schema = schema
    log.info("Strawberry GraphQL schema initialized")


async def shutdown(app: web.Application) -> None:
    """Shutdown Strawberry GraphQL app"""
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    """Create Strawberry GraphQL application"""
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["gql.context"] = StrawberryContext()

    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)

    # Add Strawberry GraphQL endpoints with auth
    view = StrawberryGraphQLView(schema=schema)

    @auth_required
    async def auth_wrapped_view(request):
        # Log the request
        user = request.get("user", {})
        access_key = request.get("keypair", {}).get("access_key", "unknown")
        log.info(
            "STRAWBERRY.GQL request (ak:{}, user:{})", access_key, user.get("username", "unknown")
        )

        return await view(request)

    cors.add(app.router.add_route("POST", r"/artifact-registry", auth_wrapped_view))
    cors.add(app.router.add_route("GET", r"/artifact-registry", auth_wrapped_view))  # For GraphiQL

    return app, []
