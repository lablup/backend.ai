from __future__ import annotations

from typing import Any, Dict, Final, Optional, Tuple

import aiohttp
import yarl

from ai.backend.common.request import (
    FolderCloneRequest,
    FolderCreateRequest,
    FolderDeleteRequest,
    FolderFileDeleteRequest,
    FolderFileDownloadRequest,
    FolderFileFetchRequest,
    FolderFileListRequest,
    FolderFileMkdirRequest,
    FolderFileMoveRequest,
    FolderFileRenameRequest,
    FolderFileUploadRequest,
    FolderMountRequest,
    FolderUsageRequest,
    FolderUsedBytesRequest,
    QuotaScopeDeleteQuotaRequest,
    QuotaScopeRequest,
    QuotaScopeUpdateRequest,
    VolumeFsUsageRequest,
    VolumeHwinfoRequest,
    VolumePerformanceMetricRequest,
    VolumeQuotaRequest,
    VolumeQuotaUpdateRequest,
)
from ai.backend.common.response import (
    FolderFileDownloadResponse,
    FolderFileListResponse,
    FolderFileUploadResponse,
    FolderMountResponse,
    FolderUsageResponse,
    FolderUsedBytesResponse,
    QuotaScopeResponse,
    VolumeFsUsageResponse,
    VolumeHwinfoResponse,
    VolumePerformanceMetricResponse,
    VolumeQuotaResponse,
    VolumesResponse,
)
from ai.backend.manager.errors.storage import (
    StorageRequestError,
    StorageResourceGoneError,
)

AUTH_TOKEN_HDR: Final = "X-BackendAI-Storage-Auth-Token"


class StorageProxyClient:
    """Client for communicating with Backend.AI storage proxy servers."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        secret: str,
        manager_api_url: yarl.URL,
    ) -> None:
        self.session = session
        self.secret = secret
        self.manager_api_url = manager_api_url

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Make an authenticated request to the storage proxy."""
        headers = kwargs.pop("headers", {})
        headers[AUTH_TOKEN_HDR] = self.secret

        url = self.manager_api_url / endpoint
        async with self.session.request(
            method,
            url,
            json=json,
            headers=headers,
            **kwargs,
        ) as resp:
            if resp.status // 100 != 2:
                try:
                    error_data = await resp.json()
                    message = error_data.pop("msg", None)
                    if resp.status == 410:
                        raise StorageResourceGoneError(
                            extra_msg=message,
                            extra_data=error_data,
                        )
                    raise StorageRequestError(
                        extra_msg=message,
                        extra_data=error_data,
                    )
                except Exception:
                    if resp.status == 410:
                        raise StorageResourceGoneError()
                    raise StorageRequestError(
                        extra_msg=f"Storage proxy responded with {resp.status} {resp.reason}",
                    )
            return resp

    # Volume operations
    async def get_volumes(self) -> VolumesResponse:
        """Get list of all volumes."""
        async with await self._request("GET", "volumes") as resp:
            data = await resp.json()
            return VolumesResponse(**data)

    async def get_volume_performance_metric(
        self, request: VolumePerformanceMetricRequest
    ) -> VolumePerformanceMetricResponse:
        """Get performance metrics for a volume."""
        async with await self._request(
            "GET", "volume/performance-metric", json=request.model_dump()
        ) as resp:
            data = await resp.json()
            return VolumePerformanceMetricResponse(**data)

    async def get_volume_hwinfo(self, request: VolumeHwinfoRequest) -> VolumeHwinfoResponse:
        """Get hardware information for a volume."""
        async with await self._request("GET", "volume/hwinfo", json=request.model_dump()) as resp:
            data = await resp.json()
            return VolumeHwinfoResponse(**data)

    async def get_volume_quota(self, request: VolumeQuotaRequest) -> VolumeQuotaResponse:
        """Get quota information for a volume."""
        async with await self._request("GET", "volume/quota", json=request.model_dump()) as resp:
            data = await resp.json()
            return VolumeQuotaResponse(**data)

    async def update_volume_quota(self, request: VolumeQuotaUpdateRequest) -> None:
        """Update volume quota."""
        async with await self._request("PATCH", "volume/quota", json=request.model_dump()):
            pass

    # Folder operations
    async def create_folder(self, request: FolderCreateRequest) -> None:
        """Create a new folder."""
        async with await self._request(
            "POST", "folder/create", json=request.model_dump(exclude_none=True)
        ):
            pass

    async def clone_folder(self, request: FolderCloneRequest) -> None:
        """Clone a folder."""
        async with await self._request(
            "POST", "folder/clone", json=request.model_dump(exclude_none=True)
        ):
            pass

    async def delete_folder(self, request: FolderDeleteRequest) -> None:
        """Delete a folder."""
        async with await self._request("POST", "folder/delete", json=request.model_dump()):
            pass

    async def get_folder_fs_usage(self, request: VolumeFsUsageRequest) -> VolumeFsUsageResponse:
        """Get filesystem usage statistics."""
        async with await self._request("GET", "folder/fs-usage", json=request.model_dump()) as resp:
            data = await resp.json()
            return VolumeFsUsageResponse(**data)

    async def get_folder_usage(self, request: FolderUsageRequest) -> FolderUsageResponse:
        """Get folder usage information."""
        async with await self._request("GET", "folder/usage", json=request.model_dump()) as resp:
            data = await resp.json()
            return FolderUsageResponse(**data)

    async def get_folder_used_bytes(
        self, request: FolderUsedBytesRequest
    ) -> FolderUsedBytesResponse:
        """Get used bytes for a folder."""
        async with await self._request(
            "GET", "folder/used-bytes", json=request.model_dump()
        ) as resp:
            data = await resp.json()
            return FolderUsedBytesResponse(**data)

    async def get_folder_mount(self, request: FolderMountRequest) -> FolderMountResponse:
        """Get mount path for a folder."""
        async with await self._request("GET", "folder/mount", json=request.model_dump()) as resp:
            data = await resp.json()
            return FolderMountResponse(**data)

    # File operations
    async def upload_file(
        self, request: FolderFileUploadRequest
    ) -> Tuple[yarl.URL, FolderFileUploadResponse]:
        """Initiate file upload."""
        async with await self._request(
            "POST", "folder/file/upload", json=request.model_dump(exclude_none=True)
        ) as resp:
            data = await resp.json()
            # Return the client URL for direct upload
            client_url = yarl.URL(resp.headers.get("X-BackendAI-Storage-Proxy-Client-URL", ""))
            return client_url, FolderFileUploadResponse(**data)

    async def download_file(
        self, request: FolderFileDownloadRequest
    ) -> Tuple[yarl.URL, FolderFileDownloadResponse]:
        """Initiate file download."""
        async with await self._request(
            "POST", "folder/file/download", json=request.model_dump(exclude_none=True)
        ) as resp:
            data = await resp.json()
            # Return the client URL for direct download
            client_url = yarl.URL(resp.headers.get("X-BackendAI-Storage-Proxy-Client-URL", ""))
            return client_url, FolderFileDownloadResponse(**data)

    async def list_files(self, request: FolderFileListRequest) -> FolderFileListResponse:
        """List files in a folder."""
        async with await self._request(
            "POST", "folder/file/list", json=request.model_dump()
        ) as resp:
            data = await resp.json()
            return FolderFileListResponse(**data)

    async def rename_file(self, request: FolderFileRenameRequest) -> None:
        """Rename a file."""
        async with await self._request("POST", "folder/file/rename", json=request.model_dump()):
            pass

    async def delete_files(self, request: FolderFileDeleteRequest) -> None:
        """Delete files."""
        async with await self._request(
            "POST", "folder/file/delete", json=request.model_dump(exclude_none=True)
        ):
            pass

    async def create_directory(self, request: FolderFileMkdirRequest) -> None:
        """Create directories."""
        async with await self._request(
            "POST", "folder/file/mkdir", json=request.model_dump(exclude_none=True)
        ):
            pass

    async def move_file(self, request: FolderFileMoveRequest) -> None:
        """Move files."""
        async with await self._request("POST", "folder/file/move", json=request.model_dump()):
            pass

    async def fetch_file(self, request: FolderFileFetchRequest) -> bytes:
        """Fetch file contents."""
        chunks = bytes()
        async with await self._request(
            "POST", "folder/file/fetch", json=request.model_dump()
        ) as resp:
            async for chunk in resp.content.iter_any():
                chunks += chunk
        return chunks

    # Quota scope operations
    async def get_quota_scope(self, request: QuotaScopeRequest) -> QuotaScopeResponse:
        """Get quota scope information."""
        async with await self._request("GET", "quota-scope", json=request.model_dump()) as resp:
            data = await resp.json()
            return QuotaScopeResponse(**data)

    async def update_quota_scope(self, request: QuotaScopeUpdateRequest) -> None:
        """Update quota scope."""
        async with await self._request("PATCH", "quota-scope", json=request.model_dump()):
            pass

    async def delete_quota_scope_quota(self, request: QuotaScopeDeleteQuotaRequest) -> None:
        """Delete quota scope quota."""
        async with await self._request("DELETE", "quota-scope/quota", json=request.model_dump()):
            pass
