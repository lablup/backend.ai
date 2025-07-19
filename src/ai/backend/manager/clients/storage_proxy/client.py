from typing import Optional

from ai.backend.manager.data.vfolder.types import (
    DeleteStatus,
    VFolderDeleteParams,
    VFolderDeleteResult,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import (
    VFolderGone,
    VFolderOperationFailed,
)

from .session_manager import StorageSessionManager


class StorageProxyClient:
    """
    A client for interacting with the storage proxy service.

    This class provides methods to manage storage volumes, including creating,
    deleting, and listing volumes.
    """

    def __init__(self, session_manager: StorageSessionManager):
        self._session_manager = session_manager

    def _is_unmanaged_path(self, path: Optional[str]) -> bool:
        return path is not None and path != ""

    async def delete_vfolder(self, params: VFolderDeleteParams) -> VFolderDeleteResult:
        proxy_name, volume_name = self._session_manager.get_proxy_and_volume(
            params.host, self._is_unmanaged_path(params.unmanaged_path)
        )
        try:
            async with self._session_manager.request(
                proxy_name,
                "POST",
                "folder/delete",
                json={
                    "volume": volume_name,
                    "vfid": str(params.vfolder_id),
                },
            ) as (_, resp):
                pass
        except (VFolderOperationFailed, InvalidAPIParameters) as e:
            if e.status == 410:
                return VFolderDeleteResult(params.vfolder_id, DeleteStatus.ALREADY_DELETED)
            return VFolderDeleteResult(params.vfolder_id, DeleteStatus.ERROR)
        except VFolderGone:
            return VFolderDeleteResult(params.vfolder_id, DeleteStatus.ALREADY_DELETED)
        return VFolderDeleteResult(params.vfolder_id, DeleteStatus.DELETE_ONGOING)
