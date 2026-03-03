"""Spec handler class using constructor dependency injection.

Serves OpenAPI and GraphiQL documentation endpoints.
These handlers return HTML or JSON responses directly (not APIResponse)
since they serve static documentation content.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.openapi import generate_openapi

if TYPE_CHECKING:
    from ai.backend.manager.config.provider import ManagerConfigProvider

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
\t<meta charset="UTF-8">
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

GRAPHIQL_V2_HTML = """
<html>
  <head>
    <title>Backend.AI GraphQL V2 API Reference</title>
\t<meta charset="UTF-8">
    <link href="../../static/vendor/graphiql.min.css" rel="stylesheet" />
  </head>
  <body style="margin: 0;">
    <div id="graphiql" style="height: 100vh;"></div>

    <script src="../../static/vendor/react.production.min.js"
    ></script>
    <script src="../../static/vendor/react-dom.production.min.js"
    ></script>
    <script src="../../static/vendor/graphiql.min.js"
    ></script>

    <script>
      const fetcher = GraphiQL.createFetcher({
        url: '/func/admin/gql',
        subscriptionUrl: '/func/admin/gql'
      });

      ReactDOM.render(
        React.createElement(GraphiQL, { fetcher: fetcher }),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
"""


class SpecHandler:
    """Spec API handler for documentation endpoints."""

    def __init__(self, *, config_provider: ManagerConfigProvider) -> None:
        self._config_provider = config_provider

    # ------------------------------------------------------------------
    # render_graphiql_graphene_html (GET /spec/graphiql)
    # ------------------------------------------------------------------

    async def render_graphiql_graphene_html(
        self,
        ctx: RequestCtx,
    ) -> web.StreamResponse:
        if not self._config_provider.config.api.allow_graphql_schema_introspection:
            raise GenericForbidden
        return web.Response(
            body=GRAPHIQL_HTML,
            status=HTTPStatus.OK,
            content_type="text/html",
        )

    # ------------------------------------------------------------------
    # render_graphiql_strawberry_html (GET /spec/graphiql/strawberry)
    # ------------------------------------------------------------------

    async def render_graphiql_strawberry_html(
        self,
        ctx: RequestCtx,
    ) -> web.StreamResponse:
        if not self._config_provider.config.api.allow_graphql_schema_introspection:
            raise GenericForbidden
        return web.Response(
            body=GRAPHIQL_V2_HTML,
            status=HTTPStatus.OK,
            content_type="text/html",
        )

    # ------------------------------------------------------------------
    # render_openapi_html (GET /spec/openapi)
    # ------------------------------------------------------------------

    async def render_openapi_html(
        self,
        ctx: RequestCtx,
    ) -> web.StreamResponse:
        if not self._config_provider.config.api.allow_openapi_schema_introspection:
            raise GenericForbidden
        return web.Response(
            body=OPENAPI_HTML,
            status=HTTPStatus.OK,
            content_type="text/html",
        )

    # ------------------------------------------------------------------
    # generate_openapi_spec (GET /spec/openapi/spec.json)
    # ------------------------------------------------------------------

    async def generate_openapi_spec(
        self,
        ctx: RequestCtx,
    ) -> web.StreamResponse:
        if not self._config_provider.config.api.allow_openapi_schema_introspection:
            raise GenericForbidden
        return web.json_response(generate_openapi(ctx.request.app["_root_app"]._subapps))
