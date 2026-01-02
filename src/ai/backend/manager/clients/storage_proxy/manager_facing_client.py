from __future__ import annotations

from collections.abc import Mapping
from contextlib import asynccontextmanager as actxmgr
from typing import Any, AsyncIterator, Optional
from urllib.parse import quote

import aiohttp

from ai.backend.common.dto.storage.request import (
    DeleteObjectReq,
    DownloadObjectReq,
    FileDeleteAsyncRequest,
    HuggingFaceGetCommitHashReqPathParam,
    HuggingFaceGetCommitHashReqQueryParam,
    HuggingFaceImportModelsReq,
    HuggingFaceRetrieveModelReqPathParam,
    HuggingFaceRetrieveModelReqQueryParam,
    HuggingFaceRetrieveModelsReq,
    HuggingFaceScanModelsReq,
    PresignedDownloadObjectReq,
    PresignedUploadObjectReq,
    ReservoirImportModelsReq,
    VFSDownloadFileReq,
    VFSListFilesReq,
)
from ai.backend.common.dto.storage.response import (
    FileDeleteAsyncResponse,
    HuggingFaceGetCommitHashResponse,
    HuggingFaceImportModelsResponse,
    HuggingFaceRetrieveModelResponse,
    HuggingFaceRetrieveModelsResponse,
    HuggingFaceScanModelsResponse,
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
    ReservoirImportModelsResponse,
    VFolderCloneResponse,
    VFSListFilesResponse,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.clients.storage_proxy.base import StorageProxyHTTPClient
from ai.backend.manager.config.unified import StorageProxyClientTimeoutConfig
from ai.backend.manager.defs import DEFAULT_CHUNK_SIZE
from ai.backend.manager.errors.storage import UnexpectedStorageProxyResponseError

storage_proxy_client_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.CLIENT, layer=LayerType.STORAGE_PROXY_CLIENT)),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class StorageProxyManagerFacingClient:
    """
    Client for interacting with the storage proxy manager-facing API.
    This client provides methods for administrative operations such as volume management,
    folder creation/deletion, quota management, and performance metrics.
    """

    _client: StorageProxyHTTPClient
    _timeout_config: StorageProxyClientTimeoutConfig

    def __init__(
        self,
        client: StorageProxyHTTPClient,
        timeout_config: StorageProxyClientTimeoutConfig,
    ) -> None:
        self._client = client
        self._timeout_config = timeout_config

    @storage_proxy_client_resilience.apply()
    async def get_volumes(self) -> Mapping[str, Any]:
        """
        Get all volumes from the storage proxy.

        :return: Response containing volume information
        """
        return await self._client.request_with_response(
            "GET",
            "volumes",
            timeout=self._timeout_config.get_volumes.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
        await self._client.request(
            "POST",
            "folder/create",
            body=body,
            timeout=self._timeout_config.create_folder.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.delete_folder.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
        data = await self._client.request_with_response(
            "POST",
            "folder/clone",
            body=body,
            timeout=self._timeout_config.clone_folder.to_client_timeout(),
        )
        return VFolderCloneResponse.model_validate(data)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_mount_path.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_volume_hwinfo.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_volume_performance_metric.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_fs_usage.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_volume_quota.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
        await self._client.request(
            "PATCH",
            "volume/quota",
            body=body,
            timeout=self._timeout_config.update_volume_quota.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_quota_scope.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
        await self._client.request(
            "PATCH",
            "quota-scope",
            body=body,
            timeout=self._timeout_config.update_quota_scope.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.delete_quota_scope_quota.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.mkdir.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.rename_file.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.delete_files.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
    async def delete_files_async(
        self,
        request: FileDeleteAsyncRequest,
    ) -> FileDeleteAsyncResponse:
        """
        Delete files or directories asynchronously using background tasks.

        :param request: Request containing volume, vfid, relpaths, and recursive flag
        :return: Response containing background task ID
        """
        response = await self._client.request_with_response(
            "POST",
            "folder/file/delete-async",
            body=request.model_dump(mode="json"),
            timeout=self._timeout_config.delete_files_async.to_client_timeout(),
        )
        return FileDeleteAsyncResponse.model_validate(response)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.move_file.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.upload_file.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.download_file.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.list_files.to_client_timeout(),
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
            timeout=self._timeout_config.fetch_file.to_client_timeout(),
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

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_folder_usage.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_used_bytes.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.scan_huggingface_models.to_client_timeout(),
        )
        return HuggingFaceScanModelsResponse.model_validate(resp)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.retrieve_huggingface_models.to_client_timeout(),
        )
        return HuggingFaceRetrieveModelsResponse.model_validate(resp)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.retrieve_huggingface_model.to_client_timeout(),
        )
        return HuggingFaceRetrieveModelResponse.model_validate(resp)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.import_huggingface_models.to_client_timeout(),
        )
        return HuggingFaceImportModelsResponse.model_validate(resp)

    @storage_proxy_client_resilience.apply()
    async def get_huggingface_model_commit_hash(
        self,
        path: HuggingFaceGetCommitHashReqPathParam,
        query: HuggingFaceGetCommitHashReqQueryParam,
    ) -> HuggingFaceGetCommitHashResponse:
        """
        Get the commit hash for a specific HuggingFace model revision.
        """
        params = {"registry_name": query.registry_name}
        if query.revision:
            params["revision"] = query.revision

        encoded_model_id = quote(path.model_id, safe="")
        resp = await self._client.request_with_response(
            "GET",
            f"v1/registries/huggingface/model/{encoded_model_id}/commit-hash",
            params=params,
            timeout=self._timeout_config.get_huggingface_model_commit_hash.to_client_timeout(),
        )

        return HuggingFaceGetCommitHashResponse.model_validate(resp)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.import_reservoir_models.to_client_timeout(),
        )
        return ReservoirImportModelsResponse.model_validate(resp)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.download_s3_file.to_client_timeout(),
        )

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_s3_presigned_download_url.to_client_timeout(),
        )
        return PresignedDownloadObjectResponse.model_validate(resp)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.get_s3_presigned_upload_url.to_client_timeout(),
        )
        return PresignedUploadObjectResponse.model_validate(resp)

    @storage_proxy_client_resilience.apply()
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
            timeout=self._timeout_config.delete_s3_object.to_client_timeout(),
        )

    # TODO: Support storage_proxy_client_resilience
    @actxmgr
    async def download_vfs_file_streaming(
        self,
        storage_name: str,
        req: VFSDownloadFileReq,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        """
        Download a file from VFS storage using streaming.

        :param storage_name: Name of the VFS storage
        :param req: VFS download file request
        :return: Streaming response from the storage proxy
        """
        async with self._client.request_stream_response(
            "POST",
            f"v1/storages/vfs/{storage_name}/download",
            body=req.model_dump(by_alias=True),
            timeout=self._timeout_config.download_vfs_file_streaming.to_client_timeout(),
        ) as response_stream:
            yield response_stream

    @storage_proxy_client_resilience.apply()
    async def list_vfs_files(
        self,
        storage_name: str,
        req: VFSListFilesReq,
    ) -> VFSListFilesResponse:
        """
        List files recursively in a VFS storage directory.

        :param storage_name: Name of the VFS storage
        :param req: VFS list files request
        :return: Response containing list of files with metadata
        """
        resp = await self._client.request_with_response(
            "GET",
            f"v1/storages/vfs/{storage_name}/files",
            body=req.model_dump(by_alias=True),
            timeout=self._timeout_config.list_vfs_files.to_client_timeout(),
        )
        return VFSListFilesResponse.model_validate(resp)
