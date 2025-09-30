from __future__ import annotations

from collections.abc import Mapping
from contextlib import asynccontextmanager as actxmgr
from typing import Any, AsyncIterator, Optional
from urllib.parse import quote

import aiohttp

from ai.backend.common.dto.storage.request import (
    DeleteObjectReq,
    DownloadObjectReq,
    HuggingFaceImportModelsReq,
    HuggingFaceRetrieveModelReqPathParam,
    HuggingFaceRetrieveModelReqQueryParam,
    HuggingFaceRetrieveModelsReq,
    HuggingFaceScanModelsReq,
    HuggingFaceScanModelsSyncReq,
    PresignedDownloadObjectReq,
    PresignedUploadObjectReq,
    ReservoirImportModelsReq,
)
from ai.backend.common.dto.storage.response import (
    HuggingFaceImportModelsResponse,
    HuggingFaceRetrieveModelResponse,
    HuggingFaceRetrieveModelsResponse,
    HuggingFaceScanModelsResponse,
    HuggingFaceScanModelsSyncResponse,
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
    ReservoirImportModelsResponse,
    VFolderCloneResponse,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.clients.storage_proxy.base import StorageProxyHTTPClient
from ai.backend.manager.decorators.client_decorator import create_layer_aware_client_decorator
from ai.backend.manager.defs import DEFAULT_CHUNK_SIZE
from ai.backend.manager.errors.storage import UnexpectedStorageProxyResponseError

client_decorator = create_layer_aware_client_decorator(LayerType.STORAGE_PROXY_CLIENT)


class StorageProxyManagerFacingClient:
    """
    Client for interacting with the storage proxy manager-facing API.
    This client provides methods for administrative operations such as volume management,
    folder creation/deletion, quota management, and performance metrics.
    """

    _client: StorageProxyHTTPClient

    def __init__(self, client: StorageProxyHTTPClient):
        self._client = client

    @client_decorator()
    async def get_volumes(self) -> Mapping[str, Any]:
        """
        Get all volumes from the storage proxy.

        :return: Response containing volume information
        """
        return await self._client.request_with_response("GET", "volumes")

    @client_decorator()
    async def create_folder(
        self,
        volume: str,
        vfid: str,
        max_quota_scope_size: int | None = None,
        mode: int | None = None,
    ) -> None:
        """
        Create a new folder in the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param max_quota_scope_size: Maximum size for the quota scope (optional)
        :param mode: File mode permissions (optional)
        """
        options = {}
        if max_quota_scope_size and max_quota_scope_size > 0:
            options["initial_max_size_for_quota_scope"] = max_quota_scope_size
        body: dict[str, Any] = {
            "volume": volume,
            "vfid": vfid,
            "options": options,
        }
        if mode is not None:
            body["mode"] = mode
        await self._client.request("POST", "folder/create", body=body)

    @client_decorator()
    async def delete_folder(
        self,
        volume: str,
        vfid: str,
    ) -> None:
        """
        Delete a folder from the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        """
        await self._client.request(
            "POST",
            "folder/delete",
            body={
                "volume": volume,
                "vfid": vfid,
            },
        )

    @client_decorator()
    async def clone_folder(
        self,
        src_volume: str,
        src_vfid: str,
        dst_volume: str,
        dst_vfid: str,
    ) -> VFolderCloneResponse:
        """
        Clone a folder to another location.

        :param src_volume: Source volume name
        :param src_vfid: Source virtual folder ID
        :param dst_volume: Destination volume name
        :param dst_vfid: Destination virtual folder ID
        """
        body = {
            "src_volume": src_volume,
            "src_vfid": src_vfid,
            "dst_volume": dst_volume,
            "dst_vfid": dst_vfid,
        }
        data = await self._client.request_with_response("POST", "folder/clone", body=body)
        return VFolderCloneResponse.model_validate(data)

    @client_decorator()
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
        return await self._client.request_with_response(
            "GET",
            "folder/mount",
            body={
                "volume": volume,
                "vfid": vfid,
                "subpath": subpath,
            },
        )

    @client_decorator()
    async def get_volume_hwinfo(
        self,
        volume: str,
    ) -> Mapping[str, Any]:
        """
        Get hardware information for a volume.

        :param volume: Volume name
        :return: Response containing hardware information
        """
        return await self._client.request_with_response(
            "GET",
            "volume/hwinfo",
            body={
                "volume": volume,
            },
        )

    @client_decorator()
    async def get_volume_performance_metric(
        self,
        volume: str,
    ) -> Mapping[str, Any]:
        """
        Get performance metrics for a volume.

        :param volume: Volume name
        :return: Response containing performance metrics
        """
        return await self._client.request_with_response(
            "GET",
            "volume/performance-metric",
            body={
                "volume": volume,
            },
        )

    @client_decorator()
    async def get_fs_usage(
        self,
        volume: str,
    ) -> Mapping[str, Any]:
        """
        Get filesystem usage information for a volume.

        :param volume: Volume name
        :return: Response containing filesystem usage
        """
        return await self._client.request_with_response(
            "GET",
            "folder/fs-usage",
            body={
                "volume": volume,
            },
        )

    @client_decorator()
    async def get_volume_quota(
        self,
        volume: str,
        vfid: str,
    ) -> Mapping[str, Any]:
        """
        Get quota information for a specific volume and virtual folder.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :return: Response containing quota information
        """
        return await self._client.request_with_response(
            "GET",
            "volume/quota",
            body={
                "volume": volume,
                "vfid": vfid,
            },
        )

    @client_decorator()
    async def update_volume_quota(
        self,
        volume: str,
        vfid: str,
        quota_scope_size: int,
    ) -> None:
        """
        Update the quota for a specific volume and virtual folder.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param quota_scope_size: New quota size to set
        """
        # DEPRECATED: This method is deprecated and will be removed in the future.
        body = {
            "volume": volume,
            "vfid": vfid,
            "size_bytes": quota_scope_size,
        }
        await self._client.request("PATCH", "volume/quota", body=body)

    @client_decorator()
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
        return await self._client.request_with_response(
            "GET",
            "quota-scope",
            body={
                "volume": volume,
                "qsid": qsid,
            },
        )

    @client_decorator()
    async def update_quota_scope(
        self,
        volume: str,
        qsid: str,
        max_vfolder_size: int,
    ) -> None:
        """
        Update quota scope settings.

        :param volume: Volume name
        :param qsid: Quota scope ID
        :param max_vfolder_size: Maximum size for the quota scope
        """
        body = {
            "volume": volume,
            "qsid": qsid,
            "options": {
                "limit_bytes": max_vfolder_size,
            },
        }
        await self._client.request("PATCH", "quota-scope", body=body)

    @client_decorator()
    async def delete_quota_scope_quota(
        self,
        volume: str,
        qsid: str,
    ) -> None:
        """
        Delete quota scope quota.

        :param volume: Volume name
        :param qsid: Quota scope ID
        """
        await self._client.request(
            "DELETE",
            "quota-scope/quota",
            body={
                "volume": volume,
                "qsid": qsid,
            },
        )

    @client_decorator()
    async def mkdir(
        self,
        *,
        volume: str,
        vfid: str,
        relpath: str | list[str],
        exist_ok: bool,
        parents: Optional[bool] = None,
    ) -> Mapping[str, Any]:
        """
        Create a directory in a folder.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the directory to create
        :param exist_ok: If True, do not raise an error if the directory already exists
        :param parents: If True, create parent directories as needed
        :return: Response from the storage proxy
        """
        body = {
            "volume": volume,
            "vfid": vfid,
            "relpath": relpath,
            "exist_ok": exist_ok,
        }
        if parents is not None:
            body["parents"] = parents
        return await self._client.request_with_response(
            "POST",
            "folder/file/mkdir",
            body=body,
        )

    @client_decorator()
    async def rename_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
        new_name: str,
    ) -> None:
        """
        Rename a file or directory.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Current relative path of the file/directory
        :param new_name: New name for the file/directory
        """
        await self._client.request(
            "POST",
            "folder/file/rename",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
                "new_name": new_name,
            },
        )

    @client_decorator()
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
        return await self._client.request_with_response(
            "POST",
            "folder/file/delete",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpaths": relpaths,
                "recursive": recursive,
            },
        )

    @client_decorator()
    async def move_file(
        self,
        volume: str,
        vfid: str,
        src: str,
        dst: str,
    ) -> None:
        """
        Move a file or directory.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param src: Source relative path
        :param dst: Destination relative path
        """
        await self._client.request(
            "POST",
            "folder/file/move",
            body={
                "volume": volume,
                "vfid": vfid,
                "src_relpath": src,
                "dst_relpath": dst,
            },
        )

    @client_decorator()
    async def upload_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
        size: str,
    ) -> Mapping[str, Any]:
        """
        Upload a file to the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the file
        :param size: Size of the file
        :return: Response from the storage proxy
        """
        return await self._client.request_with_response(
            "POST",
            "folder/file/upload",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
                "size": size,
            },
        )

    @client_decorator()
    async def download_file(
        self,
        *,
        volume: str,
        vfid: str,
        relpath: str,
        archive: bool = False,
        unmanaged_path: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """
        Download a file from the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the file
        :param archive: If True, download as an archive
        :param unmanaged_path: Optional unmanaged path for the file
        :return: Response from the storage proxy containing file data
        """
        return await self._client.request_with_response(
            "POST",
            "folder/file/download",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
                "archive": archive,
                "unmanaged_path": unmanaged_path,
            },
        )

    @client_decorator()
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
        return await self._client.request_with_response(
            "POST",
            "folder/file/list",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
            },
        )

    @actxmgr
    async def _fetch_file(
        self,
        volume: str,
        vfid: str,
        relpath: str,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        """
        Fetch file content from the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the file
        :return: Response from the storage proxy containing file content
        """
        async with self._client.request_stream_response(
            "POST",
            "folder/file/fetch",
            body={
                "volume": volume,
                "vfid": vfid,
                "relpath": relpath,
            },
        ) as response_stream:
            yield response_stream

    # TODO: There are some cases where `fetch_file_content` returns empty chunks are expected as successful scenarios.
    # Re-attach the commented-out decorator after refactoring the code.
    # @client_decorator()
    async def fetch_file_content(
        self,
        volume: str,
        vfid: str,
        relpath: str,
    ) -> bytes:
        """
        Fetch file content from the storage proxy.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the file
        :return: Response from the storage proxy containing file content
        """
        async with self._fetch_file(
            volume=volume,
            vfid=vfid,
            relpath=relpath,
        ) as response_stream:
            chunks = bytes()
            while True:
                chunk = await response_stream.content.read(DEFAULT_CHUNK_SIZE)
                if not chunk:
                    break
                chunks += chunk
            if not chunks:
                raise UnexpectedStorageProxyResponseError(
                    f"No content received for {volume}/{vfid}/{relpath}"
                )
            return chunks

    # TODO: Support AsyncIterator for `client_decorator`
    async def fetch_file_content_streaming(
        self,
        volume: str,
        vfid: str,
        relpath: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> AsyncIterator[bytes]:
        """
        Fetch file content from the storage proxy as a byte-stream.

        :param volume: Volume name
        :param vfid: Virtual folder ID
        :param relpath: Relative path of the file
        :param chunk_size: Size of each chunk to read
        :yield: Chunks of bytes
        """
        async with self._fetch_file(volume=volume, vfid=vfid, relpath=relpath) as resp:
            resp.raise_for_status()

            async for chunk in resp.content.iter_chunked(chunk_size):
                if not chunk:
                    break
                yield chunk

    @client_decorator()
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
        return await self._client.request_with_response(
            "GET",
            "folder/usage",
            body={
                "volume": volume,
                "vfid": vfid,
            },
        )

    @client_decorator()
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
        return await self._client.request_with_response(
            "GET",
            "folder/used-bytes",
            body={
                "volume": volume,
                "vfid": vfid,
            },
        )

    @client_decorator()
    async def scan_huggingface_models(
        self,
        req: HuggingFaceScanModelsReq,
    ) -> HuggingFaceScanModelsResponse:
        """
        Scan HuggingFace models in the specified registry.
        """
        resp = await self._client.request_with_response(
            "POST",
            "v1/registries/huggingface/scan",
            body=req.model_dump(by_alias=True),
        )
        return HuggingFaceScanModelsResponse.model_validate(resp)

    @client_decorator()
    async def scan_huggingface_models_sync(
        self,
        req: HuggingFaceScanModelsSyncReq,
    ) -> HuggingFaceScanModelsSyncResponse:
        """
        Scan HuggingFace models in the specified registry.
        """
        resp = await self._client.request_with_response(
            "POST",
            "v1/registries/huggingface/scan/sync",
            body=req.model_dump(by_alias=True),
        )
        return HuggingFaceScanModelsSyncResponse.model_validate(resp)

    @client_decorator()
    async def retrieve_huggingface_models(
        self,
        req: HuggingFaceRetrieveModelsReq,
    ) -> HuggingFaceRetrieveModelsResponse:
        """
        Retreive HuggingFace models in the specified registry.
        """
        resp = await self._client.request_with_response(
            "POST",
            "v1/registries/huggingface/models/batch",
            body=req.model_dump(by_alias=True),
        )
        return HuggingFaceRetrieveModelsResponse.model_validate(resp)

    @client_decorator()
    async def retrieve_huggingface_model(
        self,
        path: HuggingFaceRetrieveModelReqPathParam,
        query: HuggingFaceRetrieveModelReqQueryParam,
    ) -> HuggingFaceRetrieveModelResponse:
        """
        Retreive HuggingFace single model in the specified registry.
        """
        encoded_model_id = quote(path.model_id, safe="")

        resp = await self._client.request_with_response(
            "GET",
            f"v1/registries/huggingface/model/{encoded_model_id}",
            params={
                "registry_name": query.registry_name,
                "revision": query.revision,
            },
        )
        return HuggingFaceRetrieveModelResponse.model_validate(resp)

    @client_decorator()
    async def import_huggingface_models(
        self,
        req: HuggingFaceImportModelsReq,
    ) -> HuggingFaceImportModelsResponse:
        """
        Import multiple HuggingFace models into the specified registry.
        """
        resp = await self._client.request_with_response(
            "POST",
            "v1/registries/huggingface/import",
            body=req.model_dump(by_alias=True),
        )
        return HuggingFaceImportModelsResponse.model_validate(resp)

    @client_decorator()
    async def import_reservoir_models(
        self,
        req: ReservoirImportModelsReq,
    ) -> ReservoirImportModelsResponse:
        """
        Import multiple Reservoir models into the specified registry.
        """
        resp = await self._client.request(
            "POST",
            "v1/registries/reservoir/import",
            body=req.model_dump(by_alias=True),
        )
        return ReservoirImportModelsResponse.model_validate(resp)

    @client_decorator()
    async def download_s3_file(
        self,
        storage_name: str,
        bucket_name: str,
        req: DownloadObjectReq,
    ) -> None:
        """
        Download a file from S3 storage.
        """
        await self._client.request_with_response(
            "POST",
            f"v1/storages/s3/{storage_name}/buckets/{bucket_name}/object/download",
            body=req.model_dump(by_alias=True),
        )

    @client_decorator()
    async def get_s3_presigned_download_url(
        self,
        storage_name: str,
        bucket_name: str,
        req: PresignedDownloadObjectReq,
    ) -> PresignedDownloadObjectResponse:
        """
        Get a presigned URL for downloading an object from storage.
        """
        resp = await self._client.request_with_response(
            "POST",
            f"v1/storages/s3/{storage_name}/buckets/{bucket_name}/object/presigned/download",
            body=req.model_dump(by_alias=True),
        )
        return PresignedDownloadObjectResponse.model_validate(resp)

    @client_decorator()
    async def get_s3_presigned_upload_url(
        self,
        storage_name: str,
        bucket_name: str,
        req: PresignedUploadObjectReq,
    ) -> PresignedUploadObjectResponse:
        """
        Get a presigned URL for uploading an object to storage.
        """
        resp = await self._client.request_with_response(
            "POST",
            f"v1/storages/s3/{storage_name}/buckets/{bucket_name}/object/presigned/upload",
            body=req.model_dump(by_alias=True),
        )
        return PresignedUploadObjectResponse.model_validate(resp)

    @client_decorator()
    async def delete_s3_object(
        self,
        storage_name: str,
        bucket_name: str,
        req: DeleteObjectReq,
    ) -> None:
        """
        Delete a file from S3 storage.
        """
        await self._client.request(
            "DELETE",
            f"v1/storages/s3/{storage_name}/buckets/{bucket_name}/object",
            body=req.model_dump(by_alias=True),
        )
