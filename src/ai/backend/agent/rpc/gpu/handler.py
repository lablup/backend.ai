"""RPC handler for agent GPU devices (v3, pydantic-typed)."""

from __future__ import annotations

from typing import Any

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.resources import collect_device_capacities, scan_gpu_devices
from ai.backend.common.dto.agent.request import ScanGPUDevicesReq
from ai.backend.common.dto.agent.response import ScanGPUDevicesResp
from ai.backend.common.types import DeviceName


class GPURPCHandler:
    """Agent-bound RPC handler for GPU devices."""

    _agent: AbstractAgent[Any, Any]

    def __init__(self, *, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    async def scan_gpu_devices(self, req: ScanGPUDevicesReq) -> ScanGPUDevicesResp:
        del req  # empty payload; arg present only so the registry can validate it
        cuda_context = self._agent.computers.get(DeviceName("cuda"))
        devices = await scan_gpu_devices(
            {
                kernel_id: kernel.session_id
                for kernel_id, kernel in self._agent.kernel_registry.items()
            },
            self._agent.local_config.container.scratch_root,
            cuda_context.devices if cuda_context is not None else [],
            collect_device_capacities(self._agent.computers),
        )
        return ScanGPUDevicesResp(devices=devices)
