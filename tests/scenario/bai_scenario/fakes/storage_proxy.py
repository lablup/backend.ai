"""Typed fake of the storage-proxy boundary the manager talks through.

Implements ``StorageProxyManagerFacingClient`` without HTTP, keeps the folders it was
told to make, and records every call so a scenario's ``then`` can read them. What sits
below the client (aiohttp, the proxy itself) is not imitated.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import yarl

from ai.backend.common.bgtask.types import TaskID
from ai.backend.common.dto.storage.request import FileDeleteAsyncRequest
from ai.backend.common.dto.storage.response import FileDeleteAsyncResponse, VFolderCloneResponse
from ai.backend.manager.clients.storage_proxy.client_facing_info import StorageProxyClientFacingInfo
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.errors.storage import VFolderNotFound

CLONE_TASK_ID = TaskID(UUID(int=1))
"""The background task a clone answers with, so a row can state it."""
DELETE_TASK_ID = TaskID(UUID(int=2))
"""The background task a file deletion answers with."""
UPLOAD_TOKEN = "upload-token"
"""The token an upload session answers with."""
DOWNLOAD_TOKEN = "download-token"
"""The token a download session answers with."""
CLIENT_API_BASE_URL = yarl.URL("http://127.0.0.1:6021")
"""The address the fake proxy's file endpoints sit under."""

LISTED_FILES: tuple[Mapping[str, Any], ...] = (
    {
        "name": "hello.txt",
        "type": "FILE",
        "stat": {
            "size": 5,
            "mode": 33188,
            "created": "2026-01-01 00:00:00",
            "modified": "2026-01-02 00:00:00",
        },
    },
    {
        "name": "data",
        "type": "DIRECTORY",
        "stat": {
            "size": 0,
            "mode": 16877,
            "created": "2026-01-01 00:00:00",
            "modified": "2026-01-01 00:00:00",
        },
    },
)
"""What a folder answers with when its files are listed."""


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
    async def clone_folder(
        self,
        src_volume: str,
        src_vfid: str,
        dst_volume: str,
        dst_vfid: str,
    ) -> VFolderCloneResponse:
        self.calls.append(
            StorageCall(
                "clone_folder",
                src_volume,
                src_vfid,
                {"dst_volume": dst_volume, "dst_vfid": dst_vfid},
            )
        )
        self.folders[(dst_volume, dst_vfid)] = {"used_bytes": 0, "file_count": 0}
        return VFolderCloneResponse(bgtask_id=CLONE_TASK_ID)

    @override
    async def mkdir(
        self,
        *,
        volume: str,
        vfid: str,
        relpath: str | list[str],
        exist_ok: bool,
        parents: bool | None = None,
    ) -> Mapping[str, Any]:
        self.calls.append(StorageCall("mkdir", volume, vfid, {"relpath": relpath}))
        paths = [relpath] if isinstance(relpath, str) else relpath
        return {"results": list(paths)}

    @override
    async def move_file(
        self,
        volume: str,
        vfid: str,
        src: str,
        dst: str,
    ) -> None:
        self.calls.append(StorageCall("move_file", volume, vfid, {"src": src, "dst": dst}))

    @override
    async def delete_files_async(
        self,
        request: FileDeleteAsyncRequest,
    ) -> FileDeleteAsyncResponse:
        self.calls.append(
            StorageCall(
                "delete_files_async",
                request.volume,
                str(request.vfid),
                {"relpaths": [str(path) for path in request.relpaths]},
            )
        )
        return FileDeleteAsyncResponse(bgtask_id=DELETE_TASK_ID)

    @override
    async def list_files(
        self,
        volume: str,
        vfid: str,
        relpath: str,
    ) -> Mapping[str, Any]:
        self.calls.append(StorageCall("list_files", volume, vfid, {"relpath": relpath}))
        return {"items": [dict(entry) for entry in LISTED_FILES]}

    @override
    async def upload_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
        size: str,
    ) -> Mapping[str, Any]:
        self.calls.append(
            StorageCall("upload_file", volume, vfid, {"relpath": relpath, "size": size})
        )
        return {"token": UPLOAD_TOKEN}

    @override
    async def download_file(
        self,
        *,
        volume: str,
        vfid: str,
        relpath: str,
        archive: bool = False,
        unmanaged_path: str | None = None,
    ) -> Mapping[str, Any]:
        self.calls.append(
            StorageCall(
                "download_file",
                volume,
                vfid,
                {"relpath": relpath, "archive": archive},
            )
        )
        return {"token": DOWNLOAD_TOKEN}

    def created(self) -> list[StorageCall]:
        return [c for c in self.calls if c.method == "create_folder"]


class FakeStorageSessionManager(StorageSessionManager):
    """Hands out the fakes by proxy name; nothing else of the real one is needed."""

    def __init__(self, clients: Mapping[str, StorageProxyManagerFacingClient]) -> None:
        self._manager_facing_clients = dict(clients)
        self._client_facing_clients = {
            proxy_name: StorageProxyClientFacingInfo(base_url=CLIENT_API_BASE_URL)
            for proxy_name in self._manager_facing_clients
        }
        self._proxies = {}
        self._exposed_volume_info = ["percentage"]

    @override
    async def aclose(self) -> None:
        return None
