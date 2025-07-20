from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.manager.clients.storage_proxy.base import StorageProxyHTTPClient


class StorageProxyClientFacingClient:
    """
    Client for interacting with the storage proxy client-facing API.
    This client provides methods for operations that are typically exposed to end users,
    such as file operations, folder info retrieval, and download/upload operations.
    """

    _client: StorageProxyHTTPClient

    def __init__(self, client: StorageProxyHTTPClient):
        self._client = client

    async def upload_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
        size: int,
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
