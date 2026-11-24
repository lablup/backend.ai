"""The agent DataLoader paths: names resolve into uuids, each agent is answered for."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.agent.types import GPUDeviceAllocation, KernelGPUAllocation
from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.v2.agent.response import (
    AgentGPUDeviceInfo,
    AgentGPUKernelAllocationInfo,
)
from ai.backend.common.types import AgentId, DeviceId
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.actions.v2.ops.result import BulkLookupOpsResult, ScopedFieldsOpsResult
from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.data.agent.types import AgentData, AgentStatus
from ai.backend.manager.data.permission.permission_defs import AgentPermission
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.services.agent.actions.global_load_gpu_devices import (
    GlobalLoadAgentGPUDevicesActionResult,
)

READABLE = AgentId("agent-readable")
DENIED = AgentId("agent-denied")
ABSENT = AgentId("agent-absent")


def _agent(agent_id: AgentId) -> AgentData:
    return AgentData(
        uuid=AgentUUID(uuid.uuid4()),
        id=agent_id,
        status=AgentStatus.ALIVE,
        status_changed=None,
        region="local",
        resource_group="default",
        schedulable=True,
        addr="tcp://127.0.0.1:6001",
        public_host=None,
        first_contact=None,
        lost_at=None,
        version="test",
        architecture="x86_64",
        compute_plugins={},
        public_key=None,
        auto_terminate_abusing_kernel=False,
    )


@pytest.fixture
def readable() -> AgentData:
    return _agent(READABLE)


@pytest.fixture
def denied() -> AgentData:
    return _agent(DENIED)


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this agent")


@pytest.fixture
def gpu_device() -> GPUDeviceAllocation:
    return GPUDeviceAllocation(
        device_id=DeviceId("GPU-00000000-0000-0000-0000-000000000001"),
        device_index=3,
        allocated_ratio=Decimal("0.75"),
        kernel_allocations=[
            KernelGPUAllocation(
                kernel_id=KernelID(uuid.uuid4()),
                session_id=SessionID(uuid.uuid4()),
                allocated_ratio=Decimal("0.75"),
            )
        ],
    )


@pytest.fixture
def processors(
    readable: AgentData,
    denied: AgentData,
    denial: GenericForbidden,
    gpu_device: GPUDeviceAllocation,
) -> MagicMock:
    processors = MagicMock()
    processors.agent.bulk_lookup.run = AsyncMock(
        return_value=BulkLookupOpsResult(
            resolved={READABLE: readable.uuid, DENIED: denied.uuid}, failures={}, key_results=[]
        )
    )
    processors.agent.bulk_get.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[AgentData].succeeded(readable.uuid, readable),
                PartialBulkEntityResult[AgentData].denied(denied.uuid, denial),
            ]
        )
    )
    processors.agent.scoped_search_resources.run = AsyncMock(
        return_value=ScopedFieldsOpsResult(
            items=[
                AgentResourceData(
                    id=AgentResourceID(uuid.uuid4()),
                    agent_id=READABLE,
                    slot_name="cpu",
                    capacity=Decimal(4),
                    reserved=Decimal(0),
                    prereserved=Decimal(0),
                    used=Decimal(1),
                )
            ],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
    )
    processors.agent.bulk_load_container_counts.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[PartialBulkEntityResult[int].succeeded(readable.uuid, 3)]
        )
    )
    processors.agent.bulk_load_permissions.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[list[AgentPermission]].succeeded(
                    readable.uuid, [AgentPermission.READ_ATTRIBUTE]
                )
            ]
        )
    )
    processors.agent.global_load_gpu_devices.run = AsyncMock(
        return_value=GlobalLoadAgentGPUDevicesActionResult(gpu_devices={READABLE: [gpu_device]})
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> AgentAdapter:
    return AgentAdapter(processors.agent)


async def test_batch_load_answers_per_name(
    adapter: AgentAdapter,
    processors: MagicMock,
    readable: AgentData,
    denial: GenericForbidden,
) -> None:
    nodes = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    node, refused, missing = nodes
    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert node.resource_info.capacity == {"cpu": "4"}
    assert node.resource_info.used == {"cpu": "1"}
    assert node.permissions == [AgentPermission.READ_ATTRIBUTE.value]
    # A denial reaches the resolver; a name matching nothing stays None.
    assert refused is denial
    assert missing is None
    # The slot rows and the permissions are read for the agents that passed, and no other.
    search_action = processors.agent.scoped_search_resources.run.await_args.args[0]
    assert list(search_action.agent_uuids) == [readable.uuid]
    permission_action = processors.agent.bulk_load_permissions.run.await_args.args[0]
    assert list(permission_action.agent_uuids) == [readable.uuid]


async def test_container_counts_answer_per_name(
    adapter: AgentAdapter,
    processors: MagicMock,
    readable: AgentData,
    denial: GenericForbidden,
) -> None:
    counts = await adapter.batch_load_container_counts([READABLE, DENIED, ABSENT])

    assert counts == [3, denial, 0]
    count_action = processors.agent.bulk_load_container_counts.run.await_args.args[0]
    assert list(count_action.agent_uuids) == [readable.uuid]


async def test_gpu_devices_answer_per_name(
    adapter: AgentAdapter, gpu_device: GPUDeviceAllocation
) -> None:
    gpu_devices = await adapter.batch_load_gpu_devices([READABLE, ABSENT])

    [kernel_allocation] = gpu_device.kernel_allocations
    assert gpu_devices == [
        [
            AgentGPUDeviceInfo(
                device_id=gpu_device.device_id,
                device_index=gpu_device.device_index,
                allocated_ratio=gpu_device.allocated_ratio,
                kernel_allocations=[
                    AgentGPUKernelAllocationInfo(
                        kernel_id=kernel_allocation.kernel_id,
                        session_id=kernel_allocation.session_id,
                        allocated_ratio=kernel_allocation.allocated_ratio,
                    )
                ],
            )
        ],
        None,
    ]


async def test_no_names_read_nothing(adapter: AgentAdapter, processors: MagicMock) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    assert await adapter.batch_load_container_counts([]) == []
    processors.agent.bulk_lookup.run.assert_not_awaited()
