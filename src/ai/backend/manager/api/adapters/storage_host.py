"""Storage host adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.storage_host.response import (
    MyStorageHostPermissionsPayload,
    StorageHostPermissionNode,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.services.vfolder.actions.get_my_storage_host_permissions import (
    GetMyStorageHostPermissionsAction,
    StorageHostPermissionEntry,
)

from .base import BaseAdapter


class StorageHostAdapter(BaseAdapter):
    """Adapter for storage host queries."""

    async def my_storage_host_permissions(self) -> MyStorageHostPermissionsPayload:
        """Return storage hosts the current user is allowed to use.

        Calls ``current_user()`` internally — the caller does not need to pass
        any user context.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._processors.vfolder.get_my_storage_host_permissions.wait_for_complete(
            GetMyStorageHostPermissionsAction(
                user_uuid=me.user_id,
                domain_name=me.domain_name,
            )
        )
        return MyStorageHostPermissionsPayload(
            items=[self._entry_to_node(entry) for entry in result.items],
        )

    @staticmethod
    def _entry_to_node(entry: StorageHostPermissionEntry) -> StorageHostPermissionNode:
        return StorageHostPermissionNode(
            host=entry.host,
            permissions=list(entry.permissions),
        )
