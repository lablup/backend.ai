"""VFolder adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.vfolder.response import (
    VFolderNode,
)
from ai.backend.manager.services.vfolder.types import (
    VFolderBaseInfo,
    VFolderOwnershipInfo,
    VFolderUsageInfo,
)

from .base import BaseAdapter


class VFolderAdapter(BaseAdapter):
    """Adapter for VFolder domain operations."""

    @staticmethod
    def _service_info_to_node(
        base_info: VFolderBaseInfo,
        ownership_info: VFolderOwnershipInfo,
        usage_info: VFolderUsageInfo | None = None,
    ) -> VFolderNode:
        """Convert service-layer types to VFolderNode DTO."""
        raise NotImplementedError

    async def get(self, vfolder_id: UUID) -> VFolderNode:
        """Retrieve a single VFolder by ID."""
        raise NotImplementedError

    async def admin_search(self) -> object:
        """Admin search for VFolders with system scope."""
        raise NotImplementedError

    async def my_search(self) -> object:
        """Self-service search for VFolders using current user context."""
        raise NotImplementedError
