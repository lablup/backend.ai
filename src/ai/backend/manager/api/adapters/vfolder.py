"""VFolder adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.vfolder.response import (
    VFolderNode,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderBasicInfo as VFolderBasicInfoDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderOwnerInfo,
    VFolderPermissionInfo,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderUsageInfo as VFolderUsageInfoDTO,
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
        return VFolderNode(
            basic=VFolderBasicInfoDTO(
                id=base_info.id,
                name=base_info.name,
                host=base_info.host,
                quota_scope_id=str(base_info.quota_scope_id) if base_info.quota_scope_id else None,
                usage_mode=base_info.usage_mode,
                status=base_info.status.to_field(),
                created_at=base_info.created_at,
                last_used=None,
            ),
            permission=VFolderPermissionInfo(
                permission=base_info.mount_permission.to_field(),
                ownership_type=ownership_info.ownership_type.to_field(),
                is_owner=ownership_info.is_owner,
                cloneable=base_info.cloneable,
            ),
            owner=VFolderOwnerInfo(
                user=ownership_info.user_uuid,
                group=ownership_info.group_uuid,
                creator=ownership_info.creator_email,
            ),
            usage=VFolderUsageInfoDTO(
                num_files=usage_info.num_files,
                used_bytes=usage_info.used_bytes,
                max_size=None,
                max_files=0,
            )
            if usage_info is not None
            else None,
            unmanaged_path=base_info.unmanaged_path,
        )

    async def get(self, vfolder_id: UUID) -> VFolderNode:
        """Retrieve a single VFolder by ID."""
        raise NotImplementedError

    async def admin_search(self) -> object:
        """Admin search for VFolders with system scope."""
        raise NotImplementedError

    async def my_search(self) -> object:
        """Self-service search for VFolders using current user context."""
        raise NotImplementedError
