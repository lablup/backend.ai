import asyncio
from decimal import Decimal
from typing import override
from uuid import UUID

import orjson

from ai.backend.client.output.fields import kernel_node_fields, session_node_fields
from ai.backend.client.session import AsyncSession
from ai.backend.client.utils import (
    create_connection_field,
)
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.model_service import (
    AutoScalingRuleContext,
    CreatedModelServiceEndpointMetaContext,
    ModelServiceContext,
)
from ai.backend.test.contexts.session import ClusterContext
from ai.backend.test.templates.model_service.utils import wait_until_all_inference_sessions_ready
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import DependencyNotSet, UnexpectedFailure

_METRIC_COLLECTION_TIMEOUT = 120
_SCALE_TIMEOUT = 30


class ScaleOutByCPUAutoScalingRule(TestCode):
    @override
    async def test(self) -> None:
        endpoint_meta = CreatedModelServiceEndpointMetaContext.current()
        service_id = endpoint_meta.service_id
        client_session = ClientSessionContext.current()
        model_service_dep = ModelServiceContext.current()
        auto_scaling_rule = AutoScalingRuleContext.current()
        cluster_config = ClusterContext.current()
        if auto_scaling_rule is None:
            raise DependencyNotSet("AutoScalingRuleContext must be set in ModelServiceContext")

        max_replicas = auto_scaling_rule.max_replicas
        if max_replicas is None:
            raise DependencyNotSet("AutoScalingRuleContext.max_replicas must be set")

        if model_service_dep.replicas >= max_replicas:
            raise UnexpectedFailure(
                "ModelServiceContext.replicas must be less than max_replicas. Check test configuration."
            )

        vfolder_id = await client_session.VFolder(
            name=model_service_dep.model_vfolder_name
        ).get_id()

        session_ids = await self._get_session_ids(client_session, service_id)

        await self._make_cpu_intensive_task_in_service(
            client_session,
            session_ids,
        )

        await asyncio.wait_for(
            self._wait_until_cpu_utilization_above_threshold(
                client_session,
                session_ids,
                cluster_config.cluster_size,
                threshold=Decimal(auto_scaling_rule.threshold),
            ),
            timeout=_METRIC_COLLECTION_TIMEOUT,
        )

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

    async def _get_session_ids(self, client_session: AsyncSession, service_id: UUID) -> list[UUID]:
        result = await client_session.Service(service_id).info()
        active_routes = result["active_routes"]
        return [route["session_id"] for route in active_routes]

    async def _make_cpu_intensive_task_in_service(
        self, client_session: AsyncSession, session_ids: list[UUID]
    ) -> None:
        code = """
                def fib(n):
                    a, b = 0, 1
                    for _ in range(n):
                    a, b = b, a + b
                    return a

                while True:
                    fib(1000)
                """
        for session_id in session_ids:
            await client_session.ComputeSession.from_session_id(session_id).execute(code=code)

    async def _wait_until_cpu_utilization_above_threshold(
        self,
        client_session: AsyncSession,
        session_ids: list[UUID],
        cluster_size: int,
        threshold: Decimal,
    ) -> None:
        while True:
            cpu_utils = []
            for session_id in session_ids:
                kernels = await client_session.ComputeSession.from_session_id(session_id).detail(
                    fields=(
                        session_node_fields["id"],
                        create_connection_field("kernel_nodes", (kernel_node_fields["live_stat"],)),  # type: ignore
                    )
                )
                kernels_info = kernels["kernels"]

                for kernel in kernels_info:
                    if kernel["live_stat"] is None:
                        break
                    live_stat = orjson.loads(kernel["live_stat"])
                    cpu_utils.append(float(live_stat.get("cpu_util", {}).get("pct", 0.0)))

            if len(cpu_utils) != (cluster_size * len(session_ids)):
                await asyncio.sleep(
                    5
                )  # Container metrics collections are triggered every 5 seconds
                continue
            avg_cpu_util = sum(cpu_utils) / len(cpu_utils)
            if avg_cpu_util >= threshold:
                break
