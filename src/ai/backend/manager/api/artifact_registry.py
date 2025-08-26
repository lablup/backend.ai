from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.dto.manager.request import ArtifactRegistriesSyncReq
from ai.backend.common.dto.manager.response import ArtifactRegistriesSyncResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import ProcessorsCtx, StorageSessionManagerCtx
from ai.backend.manager.services.object_storage.actions.get import GetObjectStorageAction

if TYPE_CHECKING:
    pass

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class APIHandler:
    @auth_required_for_method
    @api_handler
    async def sync(
        self,
        body: BodyParam[ArtifactRegistriesSyncReq],
        processors_ctx: ProcessorsCtx,
        storage_session_manager_ctx: StorageSessionManagerCtx,
    ) -> APIResponse:
        # 스토리지 프록시 매니저 facing client 부터 얻어온 후 그 쪽으로 요청.
        storage_id = body.parsed.storage_id
        processors = processors_ctx.processors
        storage_manager = storage_session_manager_ctx.storage_session_manager

        storage_action_result = await processors.object_storage.get.wait_for_complete(
            GetObjectStorageAction(storage_id=storage_id)
        )
        storage_data = storage_action_result.result

        storage_client = storage_manager.get_manager_facing_client(storage_data.host)

        # 여기에 presigned로 부터의 다운로드 요청을...
        storage_client.download_file()

        # remote 레저버로부터 presigned url을 구해온 후 스토리지 프록시로 전달.

        resp = ArtifactRegistriesSyncResponse()

        # 어떤 스토리지에 싱크할 건지를 같이 보내야 하니...

        # 그 이후 다른 매니저한테 이 요청을 같은 엔드포인트 sync에 그대로 쏜다.
        return APIResponse.build(status_code=200, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifact-registries"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = APIHandler()
    cors.add(app.router.add_route("PATCH", "/sync", api_handler.sync))
    return app, []
