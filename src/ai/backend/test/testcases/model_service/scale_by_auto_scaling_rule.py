import asyncio
from abc import ABC, abstractmethod
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
from ai.backend.test.templates.model_service.utils import ensure_inference_sessions_ready
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import DependencyNotSet

_METRIC_COLLECTION_TIMEOUT = 120
_SCALE_TIMEOUT = 60
_CONTAINER_METRIC_COLLECTION_INTERVAL = 5  # seconds


class _CPUAutoScalingRuleTestBase(TestCode, ABC):
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

        service_info = await client_session.Service(service_id).info()
        await self._validate_replica_configuration(service_info["replicas"], auto_scaling_rule)

        target_replicas = self._get_target_replicas(auto_scaling_rule)
        result = await client_session.Service(service_id).info()
        active_routes = result["active_routes"]
        session_ids = [route["session_id"] for route in active_routes]

        await self._execute_cpu_task(client_session, session_ids)

        await asyncio.wait_for(
            self._wait_until_cpu_threshold_condition(
                client_session,
                session_ids,
                cluster_config.cluster_size,
                threshold=Decimal(auto_scaling_rule.threshold),
            ),
            timeout=_METRIC_COLLECTION_TIMEOUT,
        )

        vfolder_id = await client_session.VFolder(
            name=model_service_dep.model_vfolder_name
        ).get_id()
        await asyncio.wait_for(
            ensure_inference_sessions_ready(
                client_session,
                service_id,
                target_replicas,
                vfolder_id,
            ),
            timeout=_SCALE_TIMEOUT,
        )

        result = await client_session.Service(service_id).info()
        assert result["replicas"] == target_replicas, (
            f"Expected replicas count: {target_replicas}, actual: {result['replicas']}"
        )
        assert result["desired_session_count"] == target_replicas, (
            f"Expected desired session count: {target_replicas}, "
            f"actual: {result['desired_session_count']}"
        )

    @abstractmethod
    async def _validate_replica_configuration(
        self, current_replica_count, auto_scaling_rule
    ) -> None:
        raise NotImplementedError(
            "Subclasses must implement _validate_replica_configuration method."
        )

    @abstractmethod
    def _get_target_replicas(self, auto_scaling_rule) -> int:
        raise NotImplementedError("Subclasses must implement _get_target_replicas method.")

    @abstractmethod
    async def _execute_cpu_task(
        self, client_session: AsyncSession, session_ids: list[UUID]
    ) -> None:
        raise NotImplementedError("Subclasses must implement _execute_cpu_task method.")

    @abstractmethod
    async def _wait_until_cpu_threshold_condition(
        self,
        client_session: AsyncSession,
        session_ids: list[UUID],
        cluster_size: int,
        threshold: Decimal,
    ) -> None:
        raise NotImplementedError(
            "Subclasses must implement _wait_until_cpu_threshold_condition method."
        )


class ScaleInByCPUAutoScalingRule(_CPUAutoScalingRuleTestBase):
    async def _validate_replica_configuration(
        self, current_replica_count, auto_scaling_rule
    ) -> None:
        min_replicas = auto_scaling_rule.min_replicas
        if min_replicas is None:
            raise DependencyNotSet("AutoScalingRuleContext.min_replicas must be set")

        if current_replica_count <= min_replicas:
            raise AssertionError(
                f"Current replicas must be greater than min_replicas(current: {current_replica_count} / min_replicas: {min_replicas}). Check test configuration or TestSpec"
            )

    def _get_target_replicas(self, auto_scaling_rule) -> int:
        return auto_scaling_rule.min_replicas

    async def _execute_cpu_task(
        self, client_session: AsyncSession, session_ids: list[UUID]
    ) -> None:
        for session_id in session_ids:
            await client_session.ComputeSession.from_session_id(session_id).interrupt()

    async def _wait_until_cpu_threshold_condition(
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
                await asyncio.sleep(_CONTAINER_METRIC_COLLECTION_INTERVAL)
                continue

            avg_cpu_util = sum(cpu_utils) / len(cpu_utils)
            if avg_cpu_util <= threshold:
                break

            await asyncio.sleep(_CONTAINER_METRIC_COLLECTION_INTERVAL)


class ScaleOutByCPUAutoScalingRule(_CPUAutoScalingRuleTestBase):
    async def _validate_replica_configuration(
        self, current_replica_count, auto_scaling_rule
    ) -> None:
        max_replicas = auto_scaling_rule.max_replicas
        if max_replicas is None:
            raise DependencyNotSet("AutoScalingRuleContext.max_replicas must be set")

        if current_replica_count >= max_replicas:
            raise AssertionError(
                f"Current replicas must be less than max_replicas(current: {current_replica_count} / max_replicas: {max_replicas}). Check test configuration or TestSpec"
            )

    def _get_target_replicas(self, auto_scaling_rule) -> int:
        return auto_scaling_rule.max_replicas

    async def _execute_cpu_task(
        self, client_session: AsyncSession, session_ids: list[UUID]
    ) -> None:
        cpu_intensive_code = """
            def fib(n):
                a, b = 0, 1
                for _ in range(n):
                    a, b = b, a + b
                return a

            while True:
                fib(1000)
        """
        for session_id in session_ids:
            await client_session.ComputeSession.from_session_id(session_id).execute(
                code=cpu_intensive_code
            )

    async def _wait_until_cpu_threshold_condition(
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
                await asyncio.sleep(_CONTAINER_METRIC_COLLECTION_INTERVAL)
                continue

            avg_cpu_util = sum(cpu_utils) / len(cpu_utils)
            if avg_cpu_util >= threshold:
                break

            await asyncio.sleep(_CONTAINER_METRIC_COLLECTION_INTERVAL)
