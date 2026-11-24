from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.agent.types import GPUDeviceAllocation
from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class GlobalLoadAgentGPUDevicesAction(BaseGlobalAction):
    """Read the scanned GPU devices of each named agent.

    The result names the kernels and sessions of every user on the agent, so SUPERADMIN
    is the gate.
    """

    agent_ids: Sequence[AgentId]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AgentEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_load_agent_gpu_devices"


@dataclass(frozen=True)
class GlobalLoadAgentGPUDevicesActionResult:
    """The GPU devices of each agent; an agent without a scan result is absent."""

    gpu_devices: Mapping[AgentId, list[GPUDeviceAllocation]]
