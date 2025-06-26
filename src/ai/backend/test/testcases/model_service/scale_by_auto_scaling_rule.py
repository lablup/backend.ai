import asyncio
from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.model_service import (
    AutoScalingRuleContext,
    CreatedModelServiceEndpointMetaContext,
    ModelServiceContext,
)
from ai.backend.test.templates.model_service.utils import wait_until_all_inference_sessions_ready
from ai.backend.test.templates.template import TestCode
from ai.backend.test.templates.vfolder.utils import get_vfolder_id_by_name
from ai.backend.test.utils.exceptions import DependencyNotSet

_SCALE_TIMEOUT = 30


class ScaleByAutoScalingRules(TestCode):
    @override
    async def test(self) -> None:
        endpoint_meta = CreatedModelServiceEndpointMetaContext.current()
        model_service_id = endpoint_meta.service_id
        client_session = ClientSessionContext.current()
        model_service_dep = ModelServiceContext.current()
        auto_scaling_rule_dep = AutoScalingRuleContext.current()
        max_replicas = auto_scaling_rule_dep.max_replicas
        if max_replicas is None:
            raise DependencyNotSet("AutoScalingRuleContext.max_replicas must be set")
        vfolder_id = await get_vfolder_id_by_name(
            client_session, model_service_dep.model_vfolder_name
        )

        await asyncio.wait_for(
            wait_until_all_inference_sessions_ready(
                client_session,
                model_service_id,
                max_replicas,
                vfolder_id,
            ),
            timeout=_SCALE_TIMEOUT,
        )

        result = await client_session.Service(model_service_id).info()
        assert result["replicas"] == max_replicas, (
            f"Expected replicas count: {max_replicas}, actual: {result['replicas']}"
        )
        assert result["desired_session_count"] == max_replicas, (
            f"Expected desired session count: {max_replicas}, "
            f"actual: {result['desired_session_count']}"
        )
