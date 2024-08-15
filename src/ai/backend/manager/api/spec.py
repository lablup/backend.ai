from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.openapi import generate_openapi

from .auth import auth_required
from .exceptions import GenericForbidden
from .types import CORSOptions, Iterable, WebMiddleware

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

OPENAPI_HTML = """
<!DOCTYPE html>
<html>
  <head>
    <title>Backend.AI REST API Reference</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>
  <body>
    <redoc spec-url="openapi/spec.json"></redoc>
    <script src="../static/vendor/spec-viewer.js"></script>
  </body>
</html>
"""


GRAPHIQL_HTML = """
<html>
  <head>
    <title>Backend.AI GraphQL API Reference</title>
	<meta charset="UTF-8">
    <link href="../static/vendor/graphiql.min.css" rel="stylesheet" />
  </head>
  <body style="margin: 0;">
    <div id="graphiql" style="height: 100vh;"></div>

    <script src="../static/vendor/react.production.min.js"
    ></script>
    <script src="../static/vendor/react-dom.production.min.js"
    ></script>
    <script src="../static/vendor/graphiql.min.js"
    ></script>

    <script>
      const fetcher = GraphiQL.createFetcher({ url: '../admin/gql' });

      ReactDOM.render(
        React.createElement(GraphiQL, { fetcher: fetcher }),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
"""


@auth_required
async def render_graphiql_html(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if not root_ctx.shared_config["api"]["allow-graphql-schema-introspection"]:
        raise GenericForbidden

    return web.Response(
        body=GRAPHIQL_HTML,
        status=200,
        content_type="text/html",
    )


@auth_required
async def render_openapi_html(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if not root_ctx.shared_config["api"]["allow-openapi-schema-introspection"]:
        raise GenericForbidden

    return web.Response(
        body=OPENAPI_HTML,
        status=200,
        content_type="text/html",
    )


@auth_required
async def generate_openapi_spec(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if not root_ctx.shared_config["api"]["allow-openapi-schema-introspection"]:
        raise GenericForbidden

    return web.json_response(generate_openapi(request.app["_root_app"]._subapps))


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    if root_ctx.shared_config["api"]["allow-openapi-schema-introspection"]:
        log.warning(
            "OpenAPI schema introspection is enabled. "
            "It is strongly advised to disable this in production setups."
        )


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "spec"
    app.on_startup.append(init)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("GET", "/graphiql", render_graphiql_html))
    cors.add(app.router.add_route("GET", "/openapi", render_openapi_html))
    cors.add(app.router.add_route("GET", "/openapi/spec.json", generate_openapi_spec))

    return app, []
