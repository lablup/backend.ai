"""Typed fake of the storage-proxy boundary the manager talks through.

Implements ``StorageProxyManagerFacingClient`` without HTTP, keeps the folders it was
told to make, and records every call so a scenario's ``then`` can read them. What sits
below the client (aiohttp, the proxy itself) is not imitated.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.dto.storage.request import (
    PresignedDownloadObjectReq,
    PresignedUploadObjectReq,
)
from ai.backend.common.dto.storage.response import (
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
)
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.errors.storage import VFolderNotFound

PRESIGNED_DOWNLOAD_BASE = "https://presigned.scenario.local/download"
PRESIGNED_UPLOAD_BASE = "https://presigned.scenario.local/upload"
PRESIGNED_UPLOAD_FIELDS = {"policy": "seeded-policy"}


@dataclass(frozen=True)
class StorageCall:
    method: str
    volume: str
    vfid: str
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StorageScript:
    """Alternative 1 for scripting the fake: per-method outcomes carried in
    ``Setup.extras["storage"]``. An exception is raised in place of the call."""

    create_folder: BaseException | None = None
    delete_folder: BaseException | None = None
    folder_usage: Mapping[str, int] | None = None
    files: Mapping[str, bytes] = field(default_factory=dict)
    """The files at the top of every folder, by name."""


class FakeStorageProxyManagerFacingClient(StorageProxyManagerFacingClient):
    folders: dict[tuple[str, str], dict[str, Any]]
    calls: list[StorageCall]
    script: StorageScript

    def __init__(self, script: StorageScript | None = None) -> None:
        # The real constructor binds an HTTP client; this one holds state instead.
        self.folders = {}
        self.calls = []
        self.script = script or StorageScript()

    @override
    async def get_volumes(self) -> Mapping[str, Any]:
        return {
            "volumes": [
                {
                    "name": "volume1",
                    "backend": "vfs",
                    "path": "/vfroot/volume1",
                    "fsprefix": "",
                    "capabilities": ["vfolder"],
                }
            ]
        }

    @override
    async def create_folder(
        self,
        volume: str,
        vfid: str,
        max_quota_scope_size: int | None = None,
        mode: int | None = None,
    ) -> None:
        self.calls.append(
            StorageCall(
                "create_folder",
                volume,
                vfid,
                {"max_quota_scope_size": max_quota_scope_size, "mode": mode},
            )
        )
        if self.script.create_folder is not None:
            raise self.script.create_folder
        self.folders[(volume, vfid)] = {"used_bytes": 0, "file_count": 0}

    @override
    async def delete_folder(self, volume: str, vfid: str) -> None:
        self.calls.append(StorageCall("delete_folder", volume, vfid))
        if self.script.delete_folder is not None:
            raise self.script.delete_folder
        if (volume, vfid) not in self.folders:
            raise VFolderNotFound(extra_data=vfid)
        del self.folders[(volume, vfid)]

    @override
    async def get_folder_usage(self, volume: str, vfid: str) -> Mapping[str, Any]:
        self.calls.append(StorageCall("get_folder_usage", volume, vfid))
        if self.script.folder_usage is not None:
            return dict(self.script.folder_usage)
        return dict(self.folders.get((volume, vfid), {"used_bytes": 0, "file_count": 0}))

    @override
    async def list_files(self, volume: str, vfid: str, relpath: str) -> Mapping[str, Any]:
        self.calls.append(StorageCall("list_files", volume, vfid, {"relpath": relpath}))
        return {"items": [{"name": name} for name in self.script.files]}

    @override
    async def fetch_file_content(self, volume: str, vfid: str, relpath: str) -> bytes:
        self.calls.append(StorageCall("fetch_file_content", volume, vfid, {"relpath": relpath}))
        name = relpath.removeprefix("./")
        if name not in self.script.files:
            raise VFolderNotFound(extra_data=relpath)
        return self.script.files[name]

    def created(self) -> list[StorageCall]:
        return [c for c in self.calls if c.method == "create_folder"]

    @override
    async def get_s3_presigned_download_url(
        self,
        storage_name: str,
        bucket_name: str,
        req: PresignedDownloadObjectReq,
    ) -> PresignedDownloadObjectResponse:
        self.calls.append(StorageCall("get_s3_presigned_download_url", storage_name, bucket_name))
        return PresignedDownloadObjectResponse(url=f"{PRESIGNED_DOWNLOAD_BASE}/{req.key}")

    @override
    async def get_s3_presigned_upload_url(
        self,
        storage_name: str,
        bucket_name: str,
        req: PresignedUploadObjectReq,
    ) -> PresignedUploadObjectResponse:
        self.calls.append(StorageCall("get_s3_presigned_upload_url", storage_name, bucket_name))
        return PresignedUploadObjectResponse(
            url=f"{PRESIGNED_UPLOAD_BASE}/{req.key}",
            fields=dict(PRESIGNED_UPLOAD_FIELDS),
        )


class FakeStorageSessionManager(StorageSessionManager):
    """Hands out the fakes by proxy name; nothing else of the real one is needed."""

    def __init__(self, clients: Mapping[str, StorageProxyManagerFacingClient]) -> None:
        self._manager_facing_clients = dict(clients)
        self._client_facing_clients = {}
        self._proxies = {}
        self._exposed_volume_info = ["percentage"]

    @override
    async def aclose(self) -> None:
        return None
