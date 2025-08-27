from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web
from pydantic import TypeAdapter

from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.client.manager_client import ManagerFacingClient
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisions,
    ArtifactRegistryType,
)
from ai.backend.manager.data.reservoir.types import ReservoirRegistryData
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.request import (
    ArtifactRegistriesScanReq,
    ArtifactRegistriesSearchReq,
)
from ai.backend.manager.dto.response import (
    ArtifactRegistriesScanResponse,
    ArtifactRegistriesSearchResponse,
)
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
)
from ai.backend.manager.services.artifact.actions.upsert_multi import UpsertArtifactsAction
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
    ) -> APIResponse:
        registry_id = body.parsed.registry_id
        processors = processors_ctx.processors

        get_registry_action_result = (
            await processors.artifact_registry.get_artifact_registry.wait_for_complete(
                GetArtifactRegistryAction(registry_id=registry_id)
            )
        )
        registry_type = get_registry_action_result.common.type
        registry_data = get_registry_action_result.result

        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                raise NotImplementedError("HuggingFace registry scanning is not implemented yet.")
            case ArtifactRegistryType.RESERVOIR:
                assert isinstance(registry_data, ReservoirRegistryData)
                remote_reservoir_client = ManagerFacingClient(registry_data=registry_data)

                offset = 0
                limit = 10
                all_artifacts: list[ArtifactDataWithRevisions] = []

                while True:
                    payload = {
                        "pagination": {
                            "offset": {"offset": offset, "limit": limit},
                        },
                    }
                    client_resp = await remote_reservoir_client.request(
                        "POST", "/artifact-registries/search", json=payload
                    )
                    RespTypeAdapter = TypeAdapter(ArtifactRegistriesSearchResponse)
                    parsed = RespTypeAdapter.validate_python(client_resp)

                    if not parsed.artifacts:
                        break

                    all_artifacts.extend(parsed.artifacts)

                    if len(parsed.artifacts) < limit:
                        break

                    offset += limit

                if all_artifacts:
                    for artifact_data in all_artifacts:
                        artifact_data.artifact.registry_id = registry_id
                        artifact_data.artifact.registry_type = ArtifactRegistryType.RESERVOIR

                    await processors.artifact.upsert.wait_for_complete(
                        UpsertArtifactsAction(data=all_artifacts)
                    )

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

        action_result = await processors.artifact.list_artifacts_with_revisions.wait_for_complete(
            ListArtifactsWithRevisionsAction(
                pagination=pagination,
                ordering=None,
                filters=None,
            )
        )

        resp = ArtifactRegistriesSearchResponse(
            artifacts=action_result.data,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


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
