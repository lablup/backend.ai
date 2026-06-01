"""RPC handler for agent hardware information (v3, pydantic-typed).

Agent-scoped: ``gather_hwinfo`` polls the compute-plugin registry owned
by the specific ``AbstractAgent`` instance the handler was constructed
for. The top-level registry invokes ``register_hwinfo_domain``'s factory
once per agent at bind time, so each agent gets its own
``HwinfoRPCHandler`` instance with the agent bound as private state.

TODO(v3-refactor): ideally ``AbstractAgent.gather_hwinfo`` (and every
``AbstractComputePlugin.get_node_hwinfo`` that feeds it) would return
``list[DeviceHardwareInfo]`` natively, eliminating the adapter loop
below. That refactor reaches into every accelerator plugin
(``HardwareMetadata`` TypedDict is defined in ``common/types.py``) and
is too large to bundle with this RPC surface change; it will be
scheduled separately.
"""

from __future__ import annotations

from typing import Any

from ai.backend.agent.agent import AbstractAgent
from ai.backend.common.dto.agent.request import GatherHwinfoReq
from ai.backend.common.dto.agent.response import (
    DeviceHardwareInfo,
    DeviceHwStatus,
    GatherHwinfoResp,
)


class HwinfoRPCHandler:
    """Agent-bound RPC handler for hardware info gathering."""

    _agent: AbstractAgent[Any, Any]

    def __init__(self, *, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    async def gather_hwinfo(self, req: GatherHwinfoReq) -> GatherHwinfoResp:
        del req  # empty payload; arg present only so the registry can validate it
        raw = await self._agent.gather_hwinfo()
        devices = [
            DeviceHardwareInfo(
                device_name=str(device_name),
                status=DeviceHwStatus(meta["status"]),
                status_info=meta.get("status_info"),
                metadata=dict(meta.get("metadata") or {}),
            )
            for device_name, meta in raw.items()
        ]
        return GatherHwinfoResp(devices=devices)
