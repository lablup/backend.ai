from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from pydantic import Field

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
)
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.bgtask.types import ManagerBgtaskName

if TYPE_CHECKING:
    from ai.backend.manager.registry import AgentRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

GPU_ALLOC_MAP_CACHE_PERIOD = 3600 * 24  # 24 hours


class RescanGPUAllocMapsManifest(BaseBackgroundTaskManifest):
    """
    Manifest for rescanning GPU allocation maps for a specific agent.
    """

    agent_id: AgentId = Field(description="Agent ID to rescan GPU allocation map")


class RescanGPUAllocMapsHandler(BaseBackgroundTaskHandler[RescanGPUAllocMapsManifest, None]):
    """
    Background task handler for rescanning GPU allocation maps.
    """

    _registry: AgentRegistry

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    @classmethod
    @override
    def name(cls) -> ManagerBgtaskName:
        return ManagerBgtaskName.RESCAN_GPU_ALLOC_MAPS  # type: ignore[return-value]

    @classmethod
    @override
    def manifest_type(cls) -> type[RescanGPUAllocMapsManifest]:
        return RescanGPUAllocMapsManifest

    @override
    async def execute(self, manifest: RescanGPUAllocMapsManifest) -> None:
        try:
            alloc_map = await self._registry.scan_gpu_alloc_map(manifest.agent_id)
            key = f"gpu_alloc_map.{manifest.agent_id}"
            await self._registry.valkey_stat.setex(
                name=key,
                value=dump_json_str(alloc_map),
                time=GPU_ALLOC_MAP_CACHE_PERIOD,
            )
            log.info("Agent {} GPU alloc map scanned successfully", manifest.agent_id)
        except Exception as e:
            log.error("Failed to scan GPU alloc map for agent {}: {}", manifest.agent_id, e)
            raise
