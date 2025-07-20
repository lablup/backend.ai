from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.manager.clients.storage_proxy.base import StorageProxyHTTPClient


class StorageProxyManagerFacingClient:
    """
    Client for interacting with the storage proxy manager-facing API.
    This client provides methods for administrative operations such as volume management,
    folder creation/deletion, quota management, and performance metrics.
    """

    _client: StorageProxyHTTPClient

    def __init__(self, client: StorageProxyHTTPClient):
        self._client = client

    async def get_volumes(self) -> Mapping[str, Any]:
        """
        Get all volumes from the storage proxy.

        :return: Response containing volume information
        """
        return await self._client.request("GET", "volumes")

    async def create_folder(
        self,
        volume: str,
        vfid: str,
        host_access_key: str,
        owner_access_key: str | None = None,
        mode: int | None = None,
    ) -> Mapping[str, Any]:
        """
        Create a new folder in the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param host_access_key: Host access key
        :param owner_access_key: Owner access key (optional)
        :param mode: File mode permissions (optional)
        :return: Response from the storage proxy
        """
        body = {
            "volume": volume,
            "vfid": vfid,
            "host_access_key": host_access_key,
        }
        if owner_access_key is not None:
            body["owner_access_key"] = owner_access_key
        if mode is not None:
            body["mode"] = str(mode)
        return await self._client.request("POST", "folder/create", body=body)

    async def delete_folder(
        self,
        volume: str,
        vfid: str,
    ) -> Mapping[str, Any]:
        """
        Delete a folder from the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :return: Response from the storage proxy
        """
        return await self._client.request(
            "POST",
            "folder/delete",
            body={
                "volume": volume,
                "vfid": vfid,
            },
        )

    async def clone_folder(
        self,
        src_volume: str,
        src_vfid: str,
        dst_volume: str,
        dst_vfid: str,
        host_access_key: str,
        owner_access_key: str | None = None,
    ) -> Mapping[str, Any]:
        """
        Clone a folder to another location.

        :param src_volume: Source volume name
        :param src_vfid: Source virtual folder ID
        :param dst_volume: Destination volume name
        :param dst_vfid: Destination virtual folder ID
        :param host_access_key: Host access key
        :param owner_access_key: Owner access key (optional)
        :return: Response from the storage proxy
        """
        body = {
            "src_volume": src_volume,
            "src_vfid": src_vfid,
            "dst_volume": dst_volume,
            "dst_vfid": dst_vfid,
            "host_access_key": host_access_key,
        }
        if owner_access_key is not None:
            body["owner_access_key"] = owner_access_key
        return await self._client.request("POST", "folder/clone", body=body)

    async def get_mount_path(
        self,
        volume: str,
        vfid: str,
        subpath: str = ".",
    ) -> Mapping[str, Any]:
        """
        Get the mount path for a folder.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param subpath: Subpath within the folder (default: ".")
        :return: Response containing the mount path
        """
        return await self._client.request(
            "GET",
            "folder/mount",
            body={
                "volume": volume,
                "vfid": vfid,
                "subpath": subpath,
            },
        )

    async def get_volume_hwinfo(
        self,
        volume: str,
    ) -> Mapping[str, Any]:
        """
        Get hardware information for a volume.

        :param volume: Volume name
        :return: Response containing hardware information
        """
        return await self._client.request(
            "GET",
            "volume/hwinfo",
            body={
                "volume": volume,
            },
        )

    async def get_volume_performance_metric(
        self,
        volume: str,
        metric: str,
    ) -> Mapping[str, Any]:
        """
        Get performance metrics for a volume.

        :param volume: Volume name
        :param metric: Metric name to retrieve
        :return: Response containing performance metrics
        """
        return await self._client.request(
            "GET",
            "volume/performance-metric",
            body={
                "volume": volume,
                "metric": metric,
            },
        )

    async def get_fs_usage(
        self,
        volume: str,
    ) -> Mapping[str, Any]:
        """
        Get filesystem usage information for a volume.

        :param volume: Volume name
        :return: Response containing filesystem usage
        """
        return await self._client.request(
            "GET",
            "folder/fs-usage",
            body={
                "volume": volume,
            },
        )

    async def get_quota_scope(
        self,
        volume: str,
        qsid: str,
    ) -> Mapping[str, Any]:
        """
        Get quota scope information.

        :param volume: Volume name
        :param qsid: Quota scope ID
        :return: Response containing quota scope information
        """
        return await self._client.request(
            "GET",
            "quota-scope",
            body={
                "volume": volume,
                "qsid": qsid,
            },
        )

    async def update_quota_scope(
        self,
        volume: str,
        qsid: str,
        quota: int | None = None,
    ) -> Mapping[str, Any]:
        """
        Update quota scope settings.

        :param volume: Volume name
        :param qsid: Quota scope ID
        :param quota: New quota value (optional)
        :return: Response from the storage proxy
        """
        body = {
            "volume": volume,
            "qsid": qsid,
        }
        if quota is not None:
            body["quota"] = str(quota)
        return await self._client.request("PATCH", "quota-scope", body=body)

    async def delete_quota_scope_quota(
        self,
        volume: str,
        qsid: str,
    ) -> Mapping[str, Any]:
        """
        Delete quota scope quota.

        :param volume: Volume name
        :param qsid: Quota scope ID
        :return: Response from the storage proxy
        """
        return await self._client.request(
            "DELETE",
            "quota-scope/quota",
            body={
                "volume": volume,
                "qsid": qsid,
            },
        )

    async def mkdir(
        self,
        volume: str,
        vfid: str,
        relpath: str | list[str],
        parents: bool = True,
        exist_ok: bool = False,
    ) -> Mapping[str, Any]:
        """
        Create a directory in a folder.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the directory to create
        :param parents: Create parent directories if they don't exist
        :param exist_ok: Don't raise error if directory already exists
        :return: Response from the storage proxy
        """
        return await self._client.request(
            "POST",
            "folder/file/mkdir",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
                "parents": parents,
                "exist_ok": exist_ok,
            },
        )

    async def rename_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
        new_name: str,
        is_dir: bool = False,
    ) -> Mapping[str, Any]:
        """
        Rename a file or directory.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Current relative path of the file/directory
        :param new_name: New name for the file/directory
        :param is_dir: Whether the target is a directory
        :return: Response from the storage proxy
        """
        return await self._client.request(
            "POST",
            "folder/file/rename",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
                "new_name": new_name,
                "is_dir": is_dir,
            },
        )

    async def delete_files(
        self,
        volume: str,
        vfid: str,
        relpaths: list[str],
        recursive: bool = False,
    ) -> Mapping[str, Any]:
        """
        Delete files or directories.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpaths: List of relative paths to delete
        :param recursive: Whether to delete directories recursively
        :return: Response from the storage proxy
        """
        return await self._client.request(
            "POST",
            "folder/file/delete",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpaths": relpaths,
                "recursive": recursive,
            },
        )

    async def move_file(
        self,
        volume: str,
        vfid: str,
        src: str,
        dst: str,
    ) -> Mapping[str, Any]:
        """
        Move a file or directory.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param src: Source relative path
        :param dst: Destination relative path
        :return: Response from the storage proxy
        """
        return await self._client.request(
            "POST",
            "folder/file/move",
            body={
                "volume": volume,
                "vfid": vfid,
                "src": src,
                "dst": dst,
            },
        )

    async def upload_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
        size: str,
        base64_encoded_data: str,
    ) -> Mapping[str, Any]:
        """
        Upload a file to the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the file
        :param size: Size of the file
        :param base64_encoded_data: Base64 encoded file data
        :return: Response from the storage proxy
        """
        return await self._client.request(
            "POST",
            "folder/file/upload",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
                "size": size,
                "data": base64_encoded_data,
            },
        )

    async def download_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
    ) -> Mapping[str, Any]:
        """
        Download a file from the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the file
        :return: Response from the storage proxy containing file data
        """
        return await self._client.request(
            "POST",
            "folder/file/download",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
            },
        )

    async def list_files(
        self,
        volume: str,
        vfid: str,
        relpath: str,
    ) -> Mapping[str, Any]:
        """
        List files in a directory.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the directory
        :return: Response from the storage proxy containing file list
        """
        return await self._client.request(
            "POST",
            "folder/file/list",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
            },
        )

    async def fetch_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
    ) -> Mapping[str, Any]:
        """
        Fetch file content from the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the file
        :return: Response from the storage proxy containing file content
        """
        return await self._client.request(
            "POST",
            "folder/file/fetch",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
            },
        )

    async def get_folder_usage(
        self,
        volume: str,
        vfid: str,
    ) -> Mapping[str, Any]:
        """
        Get usage information for a virtual folder.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :return: Response from the storage proxy containing usage information
        """
        return await self._client.request(
            "GET",
            "folder/usage",
            body={
                "volume": volume,
                "vfid": vfid,
            },
        )

    async def get_used_bytes(
        self,
        volume: str,
        vfid: str,
    ) -> Mapping[str, Any]:
        """
        Get the number of bytes used by a virtual folder.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :return: Response from the storage proxy containing used bytes
        """
        return await self._client.request(
            "GET",
            "folder/used-bytes",
            body={
                "volume": volume,
                "vfid": vfid,
            },
        )
