"""Component tests for the v2 session compute-schedule endpoint.

Exercises POST /v2/sessions/compute-schedule through the real aiohttp server,
the SDK v2 client, and a real SchedulingController against the real DB.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.scheduler.request import (
    ComputeScheduleInput,
    ComputeScheduleKernelResourceInput,
)
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.dto.manager.v2.session_options.types import AgentSelectionPolicyEnum
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.data.session.options import AgentSelectionPolicy, DefaultSessionOptions
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.session.processors import SessionProcessors

from .conftest import AgentFactoryFunc, build_session_registries

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    compute_session_processors: SessionProcessors,
) -> list[RouteRegistry]:
    """Serve v2 session routes backed by the real scheduling controller."""
    return build_session_registries(route_deps, compute_session_processors)


def _single_kernel_input(
    resource_group_id: ResourceGroupID,
    image_id: ImageID,
    *,
    cpu: str,
    mem: str,
    cluster_mode: ClusterModeEnum = ClusterModeEnum.SINGLE_NODE,
    designated_agent_ids: list[AgentId] | None = None,
    agent_selection_policy: AgentSelectionPolicyEnum | None = None,
) -> ComputeScheduleInput:
    return ComputeScheduleInput(
        kernels=[
            ComputeScheduleKernelResourceInput(
                image_id=image_id,
                resources=[
                    ResourceSlotEntryInput(resource_type="cpu", quantity=cpu),
                    ResourceSlotEntryInput(resource_type="mem", quantity=mem),
                ],
            )
        ],
        cluster_mode=cluster_mode,
        resource_group_id=resource_group_id,
        designated_agent_ids=designated_agent_ids,
        agent_selection_policy=agent_selection_policy,
    )


@pytest.fixture()
async def strict_agent_selection(
    db_engine: SAEngine,
    scaling_group_id: ResourceGroupID,
) -> None:
    """Make the test resource group enforce designated agents strictly."""
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(scaling_groups)
            .where(scaling_groups.c.id == scaling_group_id)
            .values(
                default_session_options=DefaultSessionOptions(
                    agent_selection_policy=AgentSelectionPolicy.STRICT,
                )
            )
        )


class TestComputeSchedule:
    async def test_fitting_kernel_succeeds(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(scaling_group_id, compute_image_fixture, cpu="1", mem="1073741824")
        )
        assert len(payload.results) == 1
        result = payload.results[0]
        assert result.success is True
        assert result.reason_hint is None
        assert result.requested_architecture == "x86_64"
        requested = {entry.resource_type: entry.quantity for entry in result.requested_slots}
        assert requested["cpu"] == Decimal(1)
        assert requested["mem"] == Decimal(1073741824)

    async def test_oversized_kernel_returns_reduction_hint(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        """The hint reflects the best-fitting node's shortage, not a sum over nodes."""
        await agent_factory({"cpu": "4", "mem": "34359738368"})
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                scaling_group_id, compute_image_fixture, cpu="10", mem="1073741824"
            )
        )
        result = payload.results[0]
        assert result.success is False
        assert result.reason_hint is not None
        assert result.reason_hint.required_reduction is not None
        reduction = {
            entry.resource_type: entry.quantity for entry in result.reason_hint.required_reduction
        }
        # 10 requested vs the larger agent's 8 cores: shortage vs the best
        # node is 2, not 6 (smaller node) nor 8 (sum over both nodes).
        assert reduction["cpu"] == Decimal(2)

    async def test_multi_kernel_results_correlate_by_index(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        body = ComputeScheduleInput(
            kernels=[
                ComputeScheduleKernelResourceInput(
                    image_id=compute_image_fixture,
                    resources=[
                        ResourceSlotEntryInput(resource_type="cpu", quantity="1"),
                        ResourceSlotEntryInput(resource_type="mem", quantity="1073741824"),
                    ],
                ),
                ComputeScheduleKernelResourceInput(
                    image_id=compute_image_fixture,
                    resources=[
                        ResourceSlotEntryInput(resource_type="cpu", quantity="100"),
                        ResourceSlotEntryInput(resource_type="mem", quantity="1073741824"),
                    ],
                ),
            ],
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            resource_group_id=scaling_group_id,
        )
        payload = await admin_v2_registry.session.compute_schedule(body)
        assert [result.success for result in payload.results] == [True, False]

    async def test_regular_user_can_compute_schedule(
        self,
        user_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await user_v2_registry.session.compute_schedule(
            _single_kernel_input(scaling_group_id, compute_image_fixture, cpu="1", mem="1073741824")
        )
        assert payload.results[0].success is True

    async def test_unknown_resource_group_returns_not_found(
        self,
        admin_v2_registry: V2ClientRegistry,
        compute_image_fixture: ImageID,
    ) -> None:
        unknown_rg = ResourceGroupID(uuid.uuid4())
        with pytest.raises(NotFoundError):
            await admin_v2_registry.session.compute_schedule(
                _single_kernel_input(unknown_rg, compute_image_fixture, cpu="1", mem="1073741824")
            )

    async def test_resource_group_without_agents_is_whole_request_error(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
    ) -> None:
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_v2_registry.session.compute_schedule(
                _single_kernel_input(
                    scaling_group_id, compute_image_fixture, cpu="1", mem="1073741824"
                )
            )
        assert exc_info.value.status == 503

    async def test_compute_schedule_does_not_persist_session(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
        db_engine: SAEngine,
    ) -> None:
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(scaling_group_id, compute_image_fixture, cpu="1", mem="1073741824")
        )
        async with db_engine.begin() as conn:
            count = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(SessionRow.__table__)
                .where(SessionRow.__table__.c.name == "compute-schedule")
            )
        assert count == 0


class TestComputeScheduleDesignatedAgents:
    async def test_strict_policy_limits_fitting_to_designated_agents(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
        strict_agent_selection: None,
    ) -> None:
        """A too-small designated agent fails the fit even though a larger
        undesignated agent could hold the kernel."""
        small_agent = await agent_factory({"cpu": "2", "mem": "34359738368"})
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                scaling_group_id,
                compute_image_fixture,
                cpu="4",
                mem="1073741824",
                designated_agent_ids=[AgentId(small_agent)],
            )
        )
        result = payload.results[0]
        assert result.success is False
        assert result.reason_hint is not None
        assert result.reason_hint.required_reduction is not None
        reduction = {
            entry.resource_type: entry.quantity for entry in result.reason_hint.required_reduction
        }
        assert reduction["cpu"] == Decimal(2)

    async def test_designated_agent_with_capacity_fits(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
        strict_agent_selection: None,
    ) -> None:
        await agent_factory({"cpu": "2", "mem": "34359738368"})
        large_agent = await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                scaling_group_id,
                compute_image_fixture,
                cpu="4",
                mem="1073741824",
                designated_agent_ids=[AgentId(large_agent)],
            )
        )
        assert payload.results[0].success is True

    async def test_request_policy_overrides_resource_group_default(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        """A STRICT policy in the request overrides the resource group's
        default PREFERRED policy, so a too-small designated agent fails."""
        small_agent = await agent_factory({"cpu": "2", "mem": "34359738368"})
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                scaling_group_id,
                compute_image_fixture,
                cpu="4",
                mem="1073741824",
                designated_agent_ids=[AgentId(small_agent)],
                agent_selection_policy=AgentSelectionPolicyEnum.STRICT,
            )
        )
        assert payload.results[0].success is False

    async def test_preferred_policy_falls_back_past_designated_agents(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        """Under the default PREFERRED policy a designated agent without
        capacity does not block fitting onto other agents — the same
        semantics as the real scheduling path."""
        small_agent = await agent_factory({"cpu": "2", "mem": "34359738368"})
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                scaling_group_id,
                compute_image_fixture,
                cpu="4",
                mem="1073741824",
                designated_agent_ids=[AgentId(small_agent)],
            )
        )
        assert payload.results[0].success is True
