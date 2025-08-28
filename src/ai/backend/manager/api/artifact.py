from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, api_handler
from ai.backend.common.dto.manager.response import ArtifactInstalledStoragesResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.services.artifact.actions.get_installed_storages import (
    GetInstalledStoragesAction,
)

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class APIHandler:
    @auth_required_for_method
    @api_handler
    async def get_installed_storages(
        self,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        action_result = await processors.artifact.get_installed_storages.wait_for_complete(
            GetInstalledStoragesAction()
        )

        # Convert UUID keys and values to strings for JSON serialization
        result = {str(k): str(v) for k, v in action_result.result.items()}

        resp = ArtifactInstalledStoragesResponse(installed_storages=result)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifacts"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = APIHandler()

    cors.add(app.router.add_route("GET", "/installed-storages", api_handler.get_installed_storages))

    return app, []
