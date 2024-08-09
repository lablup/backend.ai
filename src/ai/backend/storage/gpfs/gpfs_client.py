import contextlib
import json
import logging
import urllib.parse
from pathlib import Path
from ssl import SSLContext
from typing import Any, AsyncIterator, Callable, Coroutine, Dict, List, Mapping, Optional, TypeAlias

import aiohttp
from aiohttp import BasicAuth, web
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize

from ..exception import ExternalError
from .exceptions import (
    GPFSAPIError,
    GPFSInvalidBodyError,
    GPFSJobCancelledError,
    GPFSJobFailedError,
    GPFSNotFoundError,
    GPFSUnauthorizedError,
)
from .types import (
    GPFSDisk,
    GPFSFilesystem,
    GPFSJob,
    GPFSJobStatus,
    GPFSQuota,
    GPFSQuotaType,
    GPFSStoragePoolUsage,
    GPFSSystemHealthState,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

ResponseHandler: TypeAlias = Callable[
    [aiohttp.ClientResponse], Coroutine[None, None, aiohttp.ClientResponse]
]


def error_handler(inner):
    async def outer(*args, **kwargs):
        try:
            return await inner(*args, **kwargs)
        except web.HTTPBadRequest:
            raise GPFSInvalidBodyError
        except web.HTTPNotFound:
            raise GPFSNotFoundError

    return outer


async def base_response_handler(response: aiohttp.ClientResponse) -> aiohttp.ClientResponse:
    match response.status // 100:
        case 2:
            pass
        case 4:
            pass
        case 5:
            try:
                data = await response.json()
                msg_detail = str(data)
            except json.decoder.JSONDecodeError:
                msg_detail = "Unable to decode response body."
            raise ExternalError(
                f"GPFS API server error. (status code: {response.status}, detail: {msg_detail})"
            )
    return response


class GPFSAPIClient:
    api_endpoint: str
    username: str
    password: str

    ssl: Optional[bool | SSLContext]

    def __init__(
        self, endpoint: str, username: str, password: str, ssl: Optional[bool | SSLContext] = None
    ) -> None:
        self.api_endpoint = endpoint
        self.username = username
        self.password = password
        self.ssl = ssl

    @property
    def _req_header(self) -> Mapping[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _build_request(
        self,
        sess: aiohttp.ClientSession,
        method: str,
        path: str,
        body: Optional[Any] = None,
        *,
        err_handler: Optional[ResponseHandler] = None,
    ) -> aiohttp.ClientResponse:
        response_handler = err_handler or base_response_handler
        match method:
            case "GET":
                func = sess.get
            case "POST":
                func = sess.post
            case "PUT":
                func = sess.put
            case "PATCH":
                func = sess.patch
            case "DELETE":
                func = sess.delete
            case _:
                raise GPFSAPIError(f"Unsupported request method {method}")
        try:
            if method == "GET" or method == "DELETE":
                response = await func(
                    "/scalemgmt/v2" + path, headers=self._req_header, ssl=self.ssl
                )
            else:
                response = await func(
                    "/scalemgmt/v2" + path, headers=self._req_header, json=body, ssl=self.ssl
                )
            return await response_handler(response)
        except web.HTTPUnauthorized:
            raise GPFSUnauthorizedError

    async def _wait_for_job_done(self, jobs: List[GPFSJob]) -> None:
        for job_to_wait in jobs:
            async for attempt in AsyncRetrying(
                wait=wait_fixed(0.5),
                stop=stop_after_attempt(100),
                retry=retry_if_exception_type(web.HTTPNotFound),
            ):
                with attempt:
                    job = await self.get_job(job_to_wait.jobId)
                    if job.status == GPFSJobStatus.COMPLETED:
                        return
                    elif job.status == GPFSJobStatus.FAILED:
                        raise GPFSJobFailedError(
                            job.result.to_json() if job.result is not None else ""
                        )
                    elif job.status == GPFSJobStatus.CANCELLED:
                        raise GPFSJobCancelledError

    @contextlib.asynccontextmanager
    async def _build_session(self) -> AsyncIterator[aiohttp.ClientSession]:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint, auth=BasicAuth(self.username, self.password)
        ) as sess:
            yield sess

    @error_handler
    async def get_job(self, job_id: int) -> GPFSJob:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", f"/jobs/{job_id}")
            data = await response.json()
            if len(data.get("jobs", [])) == 0:
                raise GPFSNotFoundError
            return GPFSJob.from_dict(data["jobs"][0])

    @error_handler
    async def list_fs(self) -> List[GPFSFilesystem]:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", "/filesystems")
            data = await response.json()
        return [GPFSFilesystem.from_dict(fs_json) for fs_json in data["filesystems"]]

    @error_handler
    async def get_fs(self, fs_name: str) -> GPFSFilesystem:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", f"/filesystems/{fs_name}")
            data = await response.json()
        if len(data.get("filesystems", [])) == 0:
            raise GPFSNotFoundError
        return GPFSFilesystem.from_dict(data["filesystems"][0])

    @error_handler
    async def list_fs_pools(self, fs_name: str) -> List[GPFSStoragePoolUsage]:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", f"/filesystems/{fs_name}/pools")
            data = await response.json()
        if len(data.get("storagePool", [])) == 0:
            raise GPFSNotFoundError
        return [GPFSStoragePoolUsage.from_dict(x) for x in data["storagePool"]]

    @error_handler
    async def get_fs_pool(self, fs_name: str, pool_name: str) -> GPFSStoragePoolUsage:
        async with self._build_session() as sess:
            response = await self._build_request(
                sess, "GET", f"/filesystems/{fs_name}/pools/{pool_name}"
            )
            data = await response.json()
        if len(data.get("storagePool", [])) == 0:
            raise GPFSNotFoundError
        return GPFSStoragePoolUsage.from_dict(data["storagePool"][0])

    @error_handler
    async def list_fs_disks(self, fs_name: str) -> List[GPFSDisk]:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", f"/filesystems/{fs_name}/disks")
            data = await response.json()
        if len(data.get("disks", [])) == 0:
            raise GPFSNotFoundError
        return [GPFSDisk.from_dict(x) for x in data["disks"]]

    @error_handler
    async def list_quotas(
        self, fs_name: str, quota_type: GPFSQuotaType = GPFSQuotaType.FILESET
    ) -> List[GPFSQuota]:
        async with self._build_session() as sess:
            response = await self._build_request(
                sess,
                "GET",
                f"/filesystems/{fs_name}/quotas",
            )
            data = await response.json()
        return [GPFSQuota.from_dict(quota_info) for quota_info in data["quotas"]]

    @error_handler
    async def list_fileset_quotas(
        self,
        fs_name: str,
        fileset_name: str,
        quota_type: GPFSQuotaType = GPFSQuotaType.FILESET,
    ) -> List[GPFSQuota]:
        async with self._build_session() as sess:
            response = await self._build_request(
                sess,
                "GET",
                f"/filesystems/{fs_name}/quotas?filter=objectName={fileset_name}",
            )
            data = await response.json()
            log.debug("response: {}", data)
        return [GPFSQuota.from_dict(quota_info) for quota_info in data["quotas"]]

    @error_handler
    async def set_quota(
        self,
        fs_name: str,
        fileset_name: str,
        limit_bytes: int,
    ) -> None:
        limit_str = str(limit_bytes)
        body = {
            "operationType": "setQuota",
            "quotaType": GPFSQuotaType.FILESET,
            "objectName": fileset_name,
            "blockSoftLimit": limit_str,
            "blockHardLimit": limit_str,
        }
        async with self._build_session() as sess:
            response = await self._build_request(
                sess,
                "POST",
                f"/filesystems/{fs_name}/quotas",
                body,
            )
            data = await response.json()
            await self._wait_for_job_done([GPFSJob.from_dict(x) for x in data["jobs"]])

    @error_handler
    async def remove_quota(self, fs_name: str, fileset_name: str) -> None:
        await self.set_quota(fs_name, fileset_name, BinarySize(0))

    @error_handler
    async def create_fileset(
        self,
        fs_name: str,
        fileset_name: str,
        path: Optional[Path] = None,
        owner: Optional[str] = None,
        permissions: Optional[int] = None,
        create_directory=True,
    ) -> None:
        body: Dict[str, Any] = {
            "filesetName": fileset_name,
        }
        if owner is not None:
            body["owner"] = owner
        if permissions is not None:
            body["permissions"] = permissions
        if path is not None:
            body["path"] = path.as_posix()

        async with self._build_session() as sess:
            response = await self._build_request(
                sess,
                "POST",
                f"/filesystems/{fs_name}/filesets",
                body,
            )
            match response.status:
                case 200 | 201 | 202:
                    pass
                case 409:
                    log.warning(f"GPFS fileset already exists. Skip create. (name: {fileset_name})")
                    return
                case _:
                    raise ExternalError(
                        f"Cannot create GPFS fileset. status code: {response.status}"
                    )
            data = await response.json()
            await self._wait_for_job_done([GPFSJob.from_dict(x) for x in data["jobs"]])

    @error_handler
    async def remove_fileset(
        self,
        fs_name: str,
        fileset_name: str,
    ) -> None:
        async with self._build_session() as sess:
            response = await self._build_request(
                sess, "DELETE", f"/filesystems/{fs_name}/filesets/{fileset_name}"
            )
            await response.json()

    @error_handler
    async def copy_folder(
        self,
        source_fs_name: str,
        source_directory: Path,
        target_fs_name: str,
        target_directory: Path,
    ) -> None:
        encoded_source_dir = urllib.parse.urlencode({"": source_directory})[1:]
        body = {
            "targetFilesystem": target_fs_name,
            "targetFileset": "fset1",
            "targetPath": target_directory.as_posix(),
        }
        async with self._build_session() as sess:
            response = await self._build_request(
                sess,
                "PUT",
                f"/filesystems/{source_fs_name}/directoryCopy/{encoded_source_dir}",
                body,
            )
            data = await response.json()
            await self._wait_for_job_done([GPFSJob.from_dict(x) for x in data["jobs"]])

    @error_handler
    async def check_health(self) -> str:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", "/healthcheck")
            return await response.text()

    @error_handler
    async def get_cluster_info(self) -> Mapping[str, Any]:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", "/cluster")
            data = await response.json()
            return data["cluster"]

    @error_handler
    async def get_metric(
        self,
        query: str,
    ) -> Mapping[str, Any]:
        querystring = urllib.parse.urlencode({"query": query})
        async with self._build_session() as sess:
            response = await self._build_request(
                sess,
                "GET",
                f"/perfmon/data?{querystring}",
            )
            data = await response.json()
            return data

    @error_handler
    async def list_nodes(self) -> List[str]:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", "/nodes")
            data = await response.json()
            return [x["adminNodeName"] for x in data["nodes"]]

    @error_handler
    async def get_node_health(self, node_name: str) -> List[GPFSSystemHealthState]:
        async with self._build_session() as sess:
            response = await self._build_request(sess, "GET", f"/nodes/{node_name}/health/states")
            data = await response.json()
            return [GPFSSystemHealthState.from_dict(x) for x in data["states"]]
