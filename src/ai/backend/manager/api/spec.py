"""Backward-compatible shim for the spec module.

Documentation-serving handler logic has been migrated to:

* ``api.rest.spec.handler`` — SpecHandler class
* ``api.rest.spec`` — register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(which iterates ``global_subapp_pkgs``) continues to work.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from http import HTTPStatus
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import web

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.spec.handler import (
    GRAPHIQL_HTML,
    GRAPHIQL_V2_HTML,
    OPENAPI_HTML,
)
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.openapi import generate_openapi

from .auth import auth_required
from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@auth_required
async def render_graphiql_graphene_html(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if not root_ctx.config_provider.config.api.allow_graphql_schema_introspection:
        raise GenericForbidden

    return web.Response(
        body=GRAPHIQL_HTML,
        status=HTTPStatus.OK,
        content_type="text/html",
    )


async def render_graphiql_strawberry_html(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if not root_ctx.config_provider.config.api.allow_graphql_schema_introspection:
        raise GenericForbidden

    return web.Response(
        body=GRAPHIQL_V2_HTML,
        status=HTTPStatus.OK,
        content_type="text/html",
    )


@auth_required
async def render_openapi_html(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if not root_ctx.config_provider.config.api.allow_openapi_schema_introspection:
        raise GenericForbidden

    return web.Response(
        body=OPENAPI_HTML,
        status=HTTPStatus.OK,
        content_type="text/html",
    )


@auth_required
async def generate_openapi_spec(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if not root_ctx.config_provider.config.api.allow_openapi_schema_introspection:
        raise GenericForbidden

    return web.json_response(generate_openapi(request.app["_root_app"]._subapps))


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    if root_ctx.config_provider.config.api.allow_openapi_schema_introspection:
        log.warning(
            "OpenAPI schema introspection is enabled. "
            "It is strongly advised to disable this in production setups."
        )


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "spec"
    app.on_startup.append(init)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("GET", "/graphiql", render_graphiql_graphene_html))
    cors.add(app.router.add_route("GET", "/graphiql/strawberry", render_graphiql_strawberry_html))
    cors.add(app.router.add_route("GET", "/openapi", render_openapi_html))
    cors.add(app.router.add_route("GET", "/openapi/spec.json", generate_openapi_spec))

    return app, []
