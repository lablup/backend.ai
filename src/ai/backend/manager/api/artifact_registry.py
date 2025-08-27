from __future__ import annotations

import logging
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.client.manager_client import ManagerFacingClient
from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.dto.manager.request import (
    ArtifactRegistriesScanReq,
    ArtifactRegistriesSearchReq,
)
from ai.backend.common.dto.manager.response import (
    ArtifactRegistriesScanResponse,
    ArtifactRegistriesSearchResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.reservoir.types import ReservoirRegistryData
from ai.backend.manager.dto.context import ProcessorsCtx, StorageSessionManagerCtx
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact_registry.actions.common.get import (
    GetArtifactRegistryAction,
)

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class APIHandler:
    # TODO: 이걸 그대로 Dispatcher 쪽에 옮겨야...
    @auth_required_for_method
    @api_handler
    async def scan_artifacts(
        self,
        body: BodyParam[ArtifactRegistriesScanReq],
        processors_ctx: ProcessorsCtx,
        storage_session_manager_ctx: StorageSessionManagerCtx,
    ) -> APIResponse:
        # # 스토리지 프록시 매니저 facing client 부터 얻어온 후 그 쪽으로 요청.
        # storage_id = body.parsed.storage_id
        # processors = processors_ctx.processors
        # storage_manager = storage_session_manager_ctx.storage_session_manager

        # storage_action_result = await processors.object_storage.get.wait_for_complete(
        #     GetObjectStorageAction(storage_id=storage_id)
        # )
        # storage_data = storage_action_result.result

        # storage_client = storage_manager.get_manager_facing_client(storage_data.host)

        # # 우선 remote 레저버로부터 presigned url을 구해와야 함.

        # resp = ArtifactRegistriesScanResponse()

        # # 어떤 스토리지에 싱크할 건지를 같이 보내야 하니...

        # # 그 이후 다른 매니저한테 이 요청을 같은 엔드포인트 sync에 그대로 쏜다.
        # return APIResponse.build(status_code=200, response_model=resp)
        registry_id = body.parsed.registry_id
        storage_id = body.parsed.storage_id
        processors = processors_ctx.processors
        storage_manager = storage_session_manager_ctx.storage_session_manager

        registry_action_result = (
            await processors.artifact_registry.get_artifact_registry.wait_for_complete(
                GetArtifactRegistryAction(registry_id=registry_id)
            )
        )
        registry_type = registry_action_result.common.type

        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                # TODO: 허깅페이스 스캔 (scan_artifacts)
                ...
            case ArtifactRegistryType.RESERVOIR:
                # TODO:
                registry_data = registry_action_result.result
                assert isinstance(registry_data, ReservoirRegistryData)
                remote_reservoir_client = ManagerFacingClient(registry_data=registry_data)
                payload = {
                    "pagination": {
                        "offset": {"offset": 0, "limit": 10},
                    },
                }
                client_resp = await remote_reservoir_client.request(
                    "POST", "/artifact-registries/search", json=payload
                )
                print("client_resp_body!", client_resp)

        resp = ArtifactRegistriesScanResponse()
        return APIResponse.build(status_code=200, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_artifacts(
        self,
        body: BodyParam[ArtifactRegistriesSearchReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        pagination = body.parsed.pagination
        ordering = body.parsed.ordering
        filters = body.parsed.filters

        action_result = await processors.artifact.list_artifacts_with_revisions.wait_for_complete(
            ListArtifactsWithRevisionsAction(
                pagination=pagination,
                ordering=ordering,
                filters=filters,
            )
        )

        artifacts = action_result.data
        resp = ArtifactRegistriesSearchResponse(
            artifacts=artifacts,
        )
        return APIResponse.build(status_code=200, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifact-registries"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = APIHandler()
    cors.add(app.router.add_route("POST", "/scan", api_handler.scan_artifacts))
    cors.add(app.router.add_route("POST", "/search", api_handler.search_artifacts))
    return app, []
