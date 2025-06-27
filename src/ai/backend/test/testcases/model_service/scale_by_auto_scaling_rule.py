import asyncio
from typing import override
from uuid import UUID

from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.model_service import (
    AutoScalingRuleContext,
    CreatedModelServiceEndpointMetaContext,
    ModelServiceContext,
)
from ai.backend.test.templates.model_service.utils import wait_until_all_inference_sessions_ready
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import DependencyNotSet

_SCALE_TIMEOUT = 30


class ScaleByAutoScalingRules(TestCode):
    @override
    async def test(self) -> None:
        endpoint_meta = CreatedModelServiceEndpointMetaContext.current()
        service_id = endpoint_meta.service_id
        client_session = ClientSessionContext.current()
        model_service_dep = ModelServiceContext.current()
        auto_scaling_rule_dep = AutoScalingRuleContext.current()
        max_replicas = auto_scaling_rule_dep.max_replicas
        if max_replicas is None:
            raise DependencyNotSet("AutoScalingRuleContext.max_replicas must be set")
        vfolder_id = await client_session.VFolder(
            name=model_service_dep.model_vfolder_name
        ).get_id()

        await self._make_cpu_intensive_task_in_service(
            client_session,
            service_id,
            code="while True: pass",
        )

        await asyncio.sleep(5)  # Give some time for making cpu-intensive environment

        await asyncio.wait_for(
            wait_until_all_inference_sessions_ready(
                client_session,
                service_id,
                max_replicas,
                vfolder_id,
            ),
            timeout=_SCALE_TIMEOUT,
        )

        result = await client_session.Service(service_id).info()
        assert result["replicas"] == max_replicas, (
            f"Expected replicas count: {max_replicas}, actual: {result['replicas']}"
        )
        assert result["desired_session_count"] == max_replicas, (
            f"Expected desired session count: {max_replicas}, "
            f"actual: {result['desired_session_count']}"
        )

    async def _make_cpu_intensive_task_in_service(
        self, client_session: AsyncSession, service_id: UUID, code: str
    ) -> None:
        result = await client_session.Service(service_id).info()
        active_routes = result["active_routes"]
        session_ids = [route["session_id"] for route in active_routes]
        print(f"code excuted on session_ids: {session_ids}")
        for session_id in session_ids:
            await client_session.ComputeSession.from_session_id(session_id).execute(code=code)
