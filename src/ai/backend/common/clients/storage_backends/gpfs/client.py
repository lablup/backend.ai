from __future__ import annotations

import json
import logging
import urllib.parse
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from ssl import SSLContext
from typing import Any

import aiohttp
from tenacity import (
    AsyncRetrying,
    TryAgain,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from ai.backend.common.clients.storage_backends.gpfs.dto import (
    GPFSClusterInfo,
    GPFSCopyFolderRequest,
    GPFSCreateFilesetRequest,
    GPFSDisk,
    GPFSFilesetQuotasQuery,
    GPFSFilesystem,
    GPFSHealthCheck,
    GPFSJob,
    GPFSMetric,
    GPFSMetricQuery,
    GPFSNode,
    GPFSQuota,
    GPFSSetQuotaRequest,
    GPFSStoragePoolUsage,
    GPFSSystemHealthState,
)
from ai.backend.common.clients.storage_backends.gpfs.exceptions import (
    GPFSConflictError,
    GPFSForbiddenError,
    GPFSInternalError,
    GPFSInvalidBodyError,
    GPFSJobCancelledError,
    GPFSJobFailedError,
    GPFSNotFoundError,
    GPFSServiceError,
    GPFSUnauthorizedError,
)
from ai.backend.common.clients.storage_backends.gpfs.types import GPFSJobStatus, GPFSQuotaType
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_SUPPORTED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})


async def _handle_response(response: aiohttp.ClientResponse) -> None:
    match response.status // 100:
        case 2:
            pass
        case 4:
            msg_detail = ""
            try:
                data = await response.json()
                msg_detail = str(data)
            except (json.decoder.JSONDecodeError, aiohttp.ContentTypeError):
                msg_detail = "Unable to decode response body."
            extra_msg = f"status={response.status}, detail={msg_detail}"
            match response.status:
                case 400:
                    raise GPFSInvalidBodyError(extra_msg=extra_msg)
                case 401:
                    raise GPFSUnauthorizedError(extra_msg=extra_msg)
                case 403:
                    raise GPFSForbiddenError(extra_msg=extra_msg)
                case 404:
                    raise GPFSNotFoundError(extra_msg=extra_msg)
                case 409:
                    raise GPFSConflictError(extra_msg=extra_msg)
                case _:
                    raise GPFSInternalError(extra_msg=extra_msg)
        case 5:
            msg_detail = ""
            exc_to_chain = None
            try:
                data = await response.json()
                msg_detail = str(data)
            except json.decoder.JSONDecodeError as e:
                msg_detail = "Unable to decode response body."
                exc_to_chain = e
            raise GPFSServiceError(
                f"GPFS API server error. (status code: {response.status}, detail: {msg_detail})"
            ) from exc_to_chain


@dataclass
class GPFSAPIClientArgs:
    endpoint: str
    username: str
    password: str
    ssl: SSLContext | bool = False


class GPFSAPIClient:
    """IBM Storage Scale (GPFS) management REST API v2 client using HTTP basic auth."""

    _api_endpoint: str
    _username: str
    _password: str
    _ssl: SSLContext | bool
    _session: aiohttp.ClientSession

    def __init__(self, args: GPFSAPIClientArgs) -> None:
        self._api_endpoint = args.endpoint
        self._username = args.username
        self._password = args.password
        self._ssl = args.ssl
        self._session = aiohttp.ClientSession(
            base_url=self._api_endpoint,
            auth=aiohttp.BasicAuth(self._username, self._password),
        )

    async def aclose(self) -> None:
        await self._session.close()

    @property
    def _req_header(self) -> Mapping[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        if method not in _SUPPORTED_METHODS:
            raise GPFSInternalError(extra_msg=f"Unsupported request method {method}")
        json_body = None if method in ("GET", "DELETE") else body
        async with self._session.request(
            method,
            "/scalemgmt/v2" + path,
            headers=self._req_header,
            json=json_body,
            ssl=self._ssl,
        ) as response:
            await _handle_response(response)
            yield response

    async def _wait_for_job_done(self, jobs: list[GPFSJob]) -> None:
        for job_to_wait in jobs:
            async for attempt in AsyncRetrying(
                wait=wait_fixed(0.5),
                stop=stop_after_attempt(120),
                retry=retry_if_exception_type(TryAgain)
                | retry_if_exception_type(GPFSNotFoundError),
            ):
                with attempt:
                    job = await self.get_job(job_to_wait.jobId)
                    match job.status:
                        case GPFSJobStatus.RUNNING | GPFSJobStatus.CANCELLING:
                            raise TryAgain
                        case GPFSJobStatus.COMPLETED:
                            return
                        case GPFSJobStatus.FAILED:
                            raise GPFSJobFailedError(
                                job.result.model_dump_json() if job.result is not None else ""
                            )
                        case GPFSJobStatus.CANCELLED:
                            raise GPFSJobCancelledError

    async def get_job(self, job_id: int) -> GPFSJob:
        async with self._request("GET", f"/jobs/{job_id}") as response:
            data = await response.json()
        if len(data.get("jobs", [])) == 0:
            raise GPFSNotFoundError
        return GPFSJob.model_validate(data["jobs"][0])

    async def list_fs(self) -> list[GPFSFilesystem]:
        async with self._request("GET", "/filesystems") as response:
            data = await response.json()
        return [GPFSFilesystem.model_validate(fs_json) for fs_json in data["filesystems"]]

    async def get_fs(self, fs_name: str) -> GPFSFilesystem:
        async with self._request("GET", f"/filesystems/{fs_name}") as response:
            data = await response.json()
        if len(data.get("filesystems", [])) == 0:
            raise GPFSNotFoundError
        return GPFSFilesystem.model_validate(data["filesystems"][0])

    async def list_fs_pools(self, fs_name: str) -> list[GPFSStoragePoolUsage]:
        async with self._request("GET", f"/filesystems/{fs_name}/pools") as response:
            data = await response.json()
        if len(data.get("storagePool", [])) == 0:
            raise GPFSNotFoundError
        return [GPFSStoragePoolUsage.model_validate(x) for x in data["storagePool"]]

    async def get_fs_pool(self, fs_name: str, pool_name: str) -> GPFSStoragePoolUsage:
        async with self._request("GET", f"/filesystems/{fs_name}/pools/{pool_name}") as response:
            data = await response.json()
        if len(data.get("storagePool", [])) == 0:
            raise GPFSNotFoundError
        return GPFSStoragePoolUsage.model_validate(data["storagePool"][0])

    async def list_fs_disks(self, fs_name: str) -> list[GPFSDisk]:
        async with self._request("GET", f"/filesystems/{fs_name}/disks") as response:
            data = await response.json()
        if len(data.get("disks", [])) == 0:
            raise GPFSNotFoundError
        return [GPFSDisk.model_validate(x) for x in data["disks"]]

    async def list_quotas(
        self,
        fs_name: str,
        quota_type: GPFSQuotaType = GPFSQuotaType.FILESET,
    ) -> list[GPFSQuota]:
        async with self._request("GET", f"/filesystems/{fs_name}/quotas") as response:
            data = await response.json()
        return [GPFSQuota.model_validate(quota_info) for quota_info in data["quotas"]]

    async def list_fileset_quotas(
        self,
        fs_name: str,
        fileset_name: str,
        quota_type: GPFSQuotaType = GPFSQuotaType.FILESET,
    ) -> list[GPFSQuota]:
        query = GPFSFilesetQuotasQuery(filter=f"objectName={fileset_name}")
        querystring = "&".join(f"{k}={v}" for k, v in query.model_dump(mode="json").items())
        async with self._request(
            "GET",
            f"/filesystems/{fs_name}/quotas?{querystring}",
        ) as response:
            data = await response.json()
        log.debug("response: {}", data)
        return [GPFSQuota.model_validate(quota_info) for quota_info in data["quotas"]]

    async def set_quota(self, fs_name: str, request: GPFSSetQuotaRequest) -> None:
        async with self._request(
            "POST",
            f"/filesystems/{fs_name}/quotas",
            request.model_dump(mode="json", by_alias=True),
        ) as response:
            data = await response.json()
        await self._wait_for_job_done([GPFSJob.model_validate(x) for x in data["jobs"]])

    async def remove_quota(self, fs_name: str, fileset_name: str) -> None:
        await self.set_quota(
            fs_name,
            GPFSSetQuotaRequest(objectName=fileset_name, blockSoftLimit="0", blockHardLimit="0"),
        )

    async def create_fileset(self, fs_name: str, request: GPFSCreateFilesetRequest) -> None:
        try:
            async with self._request(
                "POST",
                f"/filesystems/{fs_name}/filesets",
                request.model_dump(mode="json", by_alias=True, exclude_none=True),
            ) as response:
                if response.status not in (200, 201, 202):
                    raise GPFSServiceError(
                        f"Cannot create GPFS fileset. status code: {response.status}"
                    )
                data = await response.json()
        except GPFSConflictError:
            log.debug("GPFS fileset {} already exists, skipping creation", request.filesetName)
            return
        await self._wait_for_job_done([GPFSJob.model_validate(x) for x in data["jobs"]])

    async def remove_fileset(
        self,
        fs_name: str,
        fileset_name: str,
    ) -> None:
        async with self._request(
            "DELETE", f"/filesystems/{fs_name}/filesets/{fileset_name}"
        ) as response:
            await response.json()

    async def copy_folder(
        self,
        source_fs_name: str,
        source_directory: Path,
        request: GPFSCopyFolderRequest,
    ) -> None:
        encoded_source_dir = urllib.parse.urlencode({"": source_directory})[1:]
        async with self._request(
            "PUT",
            f"/filesystems/{source_fs_name}/directoryCopy/{encoded_source_dir}",
            request.model_dump(mode="json", by_alias=True),
        ) as response:
            data = await response.json()
        await self._wait_for_job_done([GPFSJob.model_validate(x) for x in data["jobs"]])

    async def check_health(self) -> GPFSHealthCheck:
        async with self._request("GET", "/healthcheck") as response:
            return GPFSHealthCheck(text=await response.text())

    async def get_cluster_info(self) -> GPFSClusterInfo:
        async with self._request("GET", "/cluster") as response:
            data = await response.json()
        return GPFSClusterInfo.model_validate(data["cluster"])

    async def get_metric(
        self,
        query: str,
    ) -> GPFSMetric:
        querystring = urllib.parse.urlencode(GPFSMetricQuery(query=query).model_dump(mode="json"))
        async with self._request("GET", f"/perfmon/data?{querystring}") as response:
            data = await response.json()
        return GPFSMetric.model_validate(data)

    async def list_nodes(self) -> list[GPFSNode]:
        async with self._request("GET", "/nodes") as response:
            data = await response.json()
        return [GPFSNode(adminNodeName=x["adminNodeName"]) for x in data["nodes"]]

    async def get_node_health(self, node_name: str) -> list[GPFSSystemHealthState]:
        async with self._request("GET", f"/nodes/{node_name}/health/states") as response:
            data = await response.json()
        return [GPFSSystemHealthState.model_validate(x) for x in data["states"]]
