"""Placement of one session's kernels into the resource groups they name."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    AgentId,
    AgentSelectionStrategy,
    ArchName,
    PreemptionOrder,
    SessionId,
)
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    NoCompatibleAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.pool import (
    create_agent_selector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import (
    AgentInfo,
    AgentLimit,
    AgentResource,
    SlotResource,
)
from ai.backend.manager.views.sokovan.workload import ResourceRequest

_NPU_RESOURCE_GROUP_ID = ResourceGroupID(uuid.UUID(int=1))
_GPU_RESOURCE_GROUP_ID = ResourceGroupID(uuid.UUID(int=2))


def _slots(slots: Mapping[str, str]) -> dict[ResourceSlotName, Decimal]:
    return {ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}


def _cpu_requirement(resource_group_id: ResourceGroupID) -> ResourceRequirements:
    return ResourceRequirements(
        resource_group_id=resource_group_id,
        requested_slots=ResourceRequest(slots=_slots({"cpu": "1"})),
        required_architecture=ArchName("x86_64"),
        container_count=1,
    )


def _tracker(
    agent_id: str, resource_group_id: ResourceGroupID, cpu_capacity: str
) -> AgentStateTracker:
    return AgentStateTracker(
        original_agent=AgentInfo(
            agent_id=AgentId(agent_id),
            resource_group_id=resource_group_id,
            agent_addr=f"{agent_id}:6001",
            architecture=ArchName("x86_64"),
            resources=AgentResource(
                slots={
                    name: SlotResource(capacity=capacity, reserved=Decimal(0), used=Decimal(0))
                    for name, capacity in _slots({"cpu": cpu_capacity}).items()
                }
            ),
            container_count=0,
        )
    )


@pytest.fixture
def npu_session_naming_the_gpu_group() -> AgentSelectionCriteria:
    """A session of the NPU group whose second kernel names the GPU group."""
    return AgentSelectionCriteria(
        session_id=SessionId(uuid.uuid4()),
        resource_group_id=_NPU_RESOURCE_GROUP_ID,
        requirements=[
            _cpu_requirement(_NPU_RESOURCE_GROUP_ID),
            _cpu_requirement(_GPU_RESOURCE_GROUP_ID),
        ],
        agent_selection_policy=AgentSelectionPolicy.PREFERRED,
        designated_agent_ids=None,
        job_priority=0,
        victim_candidates=None,
        session_group=None,
    )


class TestResourceGroupPlacement:
    @pytest.mark.parametrize(
        "strategy",
        [AgentSelectionStrategy.CONCENTRATED, AgentSelectionStrategy.DISPERSED],
        ids=lambda strategy: strategy.value,
    )
    async def test_each_kernel_lands_in_the_group_it_names(
        self,
        npu_session_naming_the_gpu_group: AgentSelectionCriteria,
        strategy: AgentSelectionStrategy,
    ) -> None:
        """Neither strategy moves a kernel to the other group's emptier or fuller agent."""
        computation = await create_agent_selector(["cpu"]).compute_placements(
            strategy,
            [
                _tracker("npu-agent", _NPU_RESOURCE_GROUP_ID, "2"),
                _tracker("gpu-agent", _GPU_RESOURCE_GROUP_ID, "64"),
            ],
            npu_session_naming_the_gpu_group,
            AgentLimit(max_container_count=None),
            PreemptionOrder.OLDEST,
        )

        assert [s.selected_agent.agent_id for s in computation.selections] == [
            AgentId("npu-agent"),
            AgentId("gpu-agent"),
        ]

    async def test_a_named_group_without_agents_is_an_absolute_failure(
        self,
        npu_session_naming_the_gpu_group: AgentSelectionCriteria,
    ) -> None:
        with pytest.raises(NoCompatibleAgentError) as exc_info:
            await create_agent_selector(["cpu"]).compute_placements(
                AgentSelectionStrategy.CONCENTRATED,
                [_tracker("npu-agent", _NPU_RESOURCE_GROUP_ID, "64")],
                npu_session_naming_the_gpu_group,
                AgentLimit(max_container_count=None),
                PreemptionOrder.OLDEST,
            )
        assert exc_info.value.filter_name == "resource-group"
