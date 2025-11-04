from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from pydantic import Field

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
)
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.bgtask.types import ManagerBgtaskName

if TYPE_CHECKING:
    from ai.backend.manager.clients.agent.pool import AgentPool
    from ai.backend.manager.repositories.agent.repository import AgentRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RescanGPUAllocMapsManifest(BaseBackgroundTaskManifest):
    """
    Manifest for rescanning GPU allocation maps for a specific agent.
    """

    agent_id: AgentId = Field(description="Agent ID to rescan GPU allocation map")


class RescanGPUAllocMapsHandler(BaseBackgroundTaskHandler[RescanGPUAllocMapsManifest, None]):
    """
    Background task handler for rescanning GPU allocation maps.
    """

    _agent_repository: AgentRepository
    _agent_pool: AgentPool

    def __init__(
        self,
        agent_repository: AgentRepository,
        agent_pool: AgentPool,
    ) -> None:
        self._agent_repository = agent_repository
        self._agent_pool = agent_pool

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
            # Get agent data from repository (DB)
            agent_data = await self._agent_repository.get_by_id(manifest.agent_id)

            # Get agent client from pool and scan GPU allocation map
            agent_client = self._agent_pool.get_agent_client(agent_data.id)
            alloc_map = await agent_client.scan_gpu_alloc_map()

            # Store result in cache via repository
            await self._agent_repository.update_gpu_alloc_map(manifest.agent_id, alloc_map)
            log.info("Agent {} GPU alloc map scanned successfully", manifest.agent_id)
        except Exception as e:
            log.error("Failed to scan GPU alloc map for agent {}: {}", manifest.agent_id, e)
            raise
