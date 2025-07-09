import asyncio
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.model_service import (
    CreatedModelServiceEndpointMetaContext,
    ModelServiceContext,
    ModelServiceScaleContext,
    ScaledModelServiceReplicaCountContext,
)
from ai.backend.test.templates.model_service.utils import ensure_inference_sessions_ready
from ai.backend.test.templates.template import WrapperTestTemplate

_SCALE_TIMEOUT = 30


class ScaleReplicasTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "scale_replicas_template"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        model_service_dep = ModelServiceContext.current()
        model_service_meta = CreatedModelServiceEndpointMetaContext.current()
        model_service_scale = ModelServiceScaleContext.current()
        vfolder_id = await client_session.VFolder(
            name=model_service_dep.model_vfolder_name
        ).get_id()

        try:
            await client_session.Service(model_service_meta.service_id).scale(
                to=model_service_scale.desired_replicas
            )
            await asyncio.wait_for(
                ensure_inference_sessions_ready(
                    client_session,
                    model_service_meta.service_id,
                    model_service_scale.desired_replicas,
                    vfolder_id,
                ),
                timeout=_SCALE_TIMEOUT,
            )
            with ScaledModelServiceReplicaCountContext.with_current(
                model_service_scale.desired_replicas
            ):
                yield
        finally:
            await client_session.Service(model_service_meta.service_id).scale(
                to=model_service_dep.initial_replicas
            )
            await asyncio.wait_for(
                ensure_inference_sessions_ready(
                    client_session,
                    model_service_meta.service_id,
                    model_service_dep.initial_replicas,
                    vfolder_id,
                ),
                timeout=_SCALE_TIMEOUT,
            )
