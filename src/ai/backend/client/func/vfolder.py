from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, TypeAlias, TypeVar, Union

import aiohttp
import janus
from aiohttp import hdrs
from aiotusclient import client
from tenacity import (
    AsyncRetrying,
    RetryError,
    TryAgain,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm import tqdm
from yarl import URL

from ai.backend.client.output.fields import vfolder_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.common.types import ResultSet

from ..compat import current_loop
from ..config import DEFAULT_CHUNK_SIZE, MAX_INFLIGHT_CHUNKS
from ..exceptions import BackendClientError
from ..pagination import fetch_paginated_result
from ..request import Request
from .base import BaseFunction, api_function

__all__ = ("VFolder",)

_default_list_fields = (
    vfolder_fields["host"],
    vfolder_fields["name"],
    vfolder_fields["status"],
    vfolder_fields["created_at"],
    vfolder_fields["creator"],
    vfolder_fields["group_id"],
    vfolder_fields["permission"],
    vfolder_fields["ownership_type"],
    vfolder_fields["status"],
)

T = TypeVar("T")
list_: TypeAlias = list[T]


class ResponseFailed(Exception):
    pass


class VFolder(BaseFunction):
    def __init__(self, name: str, id: Optional[uuid.UUID] = None):
        self.name = name
        self.id = id

    @api_function
    @classmethod
    async def create(
        cls,
        name: str,
        host: str = None,
        unmanaged_path: str = None,
        group: str = None,
        usage_mode: str = "general",
        permission: str = "rw",
        cloneable: bool = False,
    ):
        rqst = Request("POST", "/folders")
        rqst.set_json({
            "name": name,
            "host": host,
            "unmanaged_path": unmanaged_path,
            "group": group,
            "usage_mode": usage_mode,
            "permission": permission,
            "cloneable": cloneable,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete_by_id(cls, oid):
        rqst = Request("DELETE", "/folders")
        rqst.set_json({"id": oid})
        async with rqst.fetch():
            return {}

    @api_function
    @classmethod
    async def list(cls, list_all=False):
        rqst = Request("GET", "/folders")
        rqst.set_json({"all": list_all})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        group: str = None,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of vfolders. Domain admins can only get domain vfolders.

        :param group: Fetch vfolders in a specific group.
        :param fields: Additional per-vfolder query fields to fetch.
        """
        return await fetch_paginated_result(
            "vfolder_list",
            {
                "group_id": (group, "UUID"),
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def paginated_own_list(
        cls,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of own vfolders.

        :param fields: Additional per-vfolder query fields to fetch.
        """
        return await fetch_paginated_result(
            "vfolder_own_list",
            {
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def paginated_invited_list(
        cls,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of invited vfolders.

        :param fields: Additional per-vfolder query fields to fetch.
        """
        return await fetch_paginated_result(
            "vfolder_invited_list",
            {
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def paginated_project_list(
        cls,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of invited vfolders.

        :param fields: Additional per-vfolder query fields to fetch.
        """
        return await fetch_paginated_result(
            "vfolder_project_list",
            {
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    async def _get_id_by_name(self) -> uuid.UUID:
        rqst = Request("GET", "/folders/_/id")
        rqst.set_json({
            "name": self.name,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return uuid.UUID(data["id"])

    @api_function
    @classmethod
    async def list_hosts(cls):
        rqst = Request("GET", "/folders/_/hosts")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_all_hosts(cls):
        rqst = Request("GET", "/folders/_/all_hosts")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_allowed_types(cls):
        rqst = Request("GET", "/folders/_/allowed_types")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def info(self):
        rqst = Request("GET", "/folders/{0}".format(self.name))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        rqst = Request("DELETE", "/folders/{0}".format(self.name))
        async with rqst.fetch():
            return {}

    @api_function
    async def purge(self) -> Mapping[str, Any]:
        if self.id is None:
            vfolder_id = await self._get_id_by_name()
            self.id = vfolder_id
        rqst = Request("POST", "/folders/purge")
        rqst.set_json({
            "id": self.id.hex,
        })
        async with rqst.fetch():
            return {}

    async def _restore(self) -> Mapping[str, Any]:
        if self.id is None:
            vfolder_id = await self._get_id_by_name()
            self.id = vfolder_id
        rqst = Request("POST", "/folders/restore-from-trash-bin")
        rqst.set_json({
            "id": self.id.hex,
        })
        async with rqst.fetch():
            return {}

    @api_function
    async def recover(self):
        return await self._restore()

    @api_function
    async def restore(self):
        return await self._restore()

    @api_function
    async def delete_trash(self) -> Mapping[str, Any]:
        if self.id is None:
            vfolder_id = await self._get_id_by_name()
            self.id = vfolder_id
        rqst = Request("POST", "/folders/delete-from-trash-bin")
        rqst.set_json({
            "id": self.id.hex,
        })
        async with rqst.fetch():
            return {}

    @api_function
    async def rename(self, new_name):
        rqst = Request("POST", "/folders/{0}/rename".format(self.name))
        rqst.set_json({
            "new_name": new_name,
        })
        async with rqst.fetch() as resp:
            self.name = new_name
            return await resp.text()

    def _write_file(self, file_path: Path, mode: str, q: janus._SyncQueueProxy[bytes]):
        with open(file_path, mode) as f:
            while True:
                chunk = q.get()
                if not chunk:
                    return
                f.write(chunk)
                q.task_done()

    async def _download_file(
        self,
        file_path: Path,
        download_url: URL,
        chunk_size: int,
        max_retries: int,
        show_progress: bool,
    ) -> None:
        if show_progress:
            print(f"Downloading to {file_path} ...")

        range_start = 0
        if_range: str | None = None
        file_unit = "bytes"
        file_mode = "wb"
        file_req_hdrs: dict[str, str] = {}
        try:
            async for session_attempt in AsyncRetrying(
                wait=wait_exponential(multiplier=0.02, min=0.02, max=5.0),
                stop=stop_after_attempt(max_retries),
                retry=retry_if_exception_type(TryAgain),
            ):
                with session_attempt:
                    try:
                        if if_range is not None:
                            file_req_hdrs[hdrs.IF_RANGE] = if_range
                            file_req_hdrs[hdrs.RANGE] = f"{file_unit}={range_start}-"
                        async with aiohttp.ClientSession(headers=file_req_hdrs) as client:
                            async with client.get(download_url, ssl=False) as raw_resp:
                                match raw_resp.status:
                                    case 200:
                                        # First attempt to download file or file has changed.
                                        file_mode = "wb"
                                        range_start = 0
                                    case 206:
                                        # File has not changed. Continue downloading from range_start.
                                        file_mode = "ab"
                                    case _:
                                        # Retry.
                                        raise ResponseFailed
                                size = int(raw_resp.headers["Content-Length"])
                                if_range = raw_resp.headers.get("Last-Modified")
                                q: janus.Queue[bytes] = janus.Queue(MAX_INFLIGHT_CHUNKS)
                                try:
                                    with tqdm(
                                        total=(size - range_start),
                                        unit=file_unit,
                                        unit_scale=True,
                                        unit_divisor=1024,
                                        disable=not show_progress,
                                    ) as pbar:
                                        loop = current_loop()
                                        writer_fut = loop.run_in_executor(
                                            None,
                                            self._write_file,
                                            file_path,
                                            file_mode,
                                            q.sync_q,
                                        )
                                        await asyncio.sleep(0)
                                        max_attempts = 10
                                        while True:
                                            try:
                                                async for attempt in AsyncRetrying(
                                                    wait=wait_exponential(
                                                        multiplier=0.02,
                                                        min=0.02,
                                                        max=5.0,
                                                    ),
                                                    stop=stop_after_attempt(max_attempts),
                                                    retry=retry_if_exception_type(TryAgain),
                                                ):
                                                    with attempt:
                                                        try:
                                                            chunk = await raw_resp.content.read(
                                                                chunk_size
                                                            )
                                                        except asyncio.TimeoutError:
                                                            raise TryAgain
                                            except RetryError:
                                                raise ResponseFailed
                                            range_start += len(chunk)
                                            pbar.update(len(chunk))
                                            if not chunk:
                                                break
                                            await q.async_q.put(chunk)
                                finally:
                                    await q.async_q.put(b"")
                                    await writer_fut
                                    q.close()
                                    await q.wait_closed()
                    except (
                        ResponseFailed,
                        aiohttp.ClientPayloadError,
                        aiohttp.ClientConnectorError,
                    ):
                        raise TryAgain
        except RetryError:
            raise RuntimeError(f"Downloading {file_path.name} failed after {max_retries} retries")

    @api_function
    async def download(
        self,
        relative_paths: Sequence[Union[str, Path]],
        *,
        basedir: Union[str, Path] = None,
        dst_dir: Union[str, Path] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        show_progress: bool = False,
        address_map: Optional[Mapping[str, str]] = None,
        max_retries: int = 20,
    ) -> None:
        base_path = Path.cwd() if basedir is None else Path(basedir).resolve()
        for relpath in relative_paths:
            file_path = base_path / relpath
            if file_path.exists():
                raise RuntimeError("The target file already exists", file_path.name)
            rqst = Request("POST", "/folders/{}/request-download".format(self.name))
            rqst.set_json({
                "path": str(relpath),
            })
            async with rqst.fetch() as resp:
                download_info = await resp.json()
                overriden_url = download_info["url"]
                if address_map:
                    if download_info["url"] in address_map:
                        overriden_url = address_map[download_info["url"]]
                    else:
                        raise BackendClientError(
                            "Overriding storage proxy addresses are given, "
                            "but no url matches with any of them.\n",
                        )

                params = {"token": download_info["token"]}
                if dst_dir is not None:
                    params["dst_dir"] = dst_dir
                download_url = URL(overriden_url).with_query(params)
            await self._download_file(
                file_path, download_url, chunk_size, max_retries, show_progress
            )

    async def _upload_files(
        self,
        file_paths: Sequence[Path],
        basedir: Union[str, Path] = None,
        dst_dir: Union[str, Path] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        address_map: Optional[Mapping[str, str]] = None,
    ) -> None:
        base_path = Path.cwd() if basedir is None else Path(basedir).resolve()
        for file_path in file_paths:
            if file_path.is_dir():
                raise BackendClientError(
                    f"Failed to upload {file_path}. Use recursive option to upload directories."
                )
            file_size = Path(file_path).stat().st_size
            rqst = Request("POST", "/folders/{}/request-upload".format(self.name))
            rqst.set_json({
                "path": "{}".format(str(Path(file_path).relative_to(base_path))),
                "size": int(file_size),
            })
            async with rqst.fetch() as resp:
                upload_info = await resp.json()
                overriden_url = upload_info["url"]
                if address_map:
                    if upload_info["url"] in address_map:
                        overriden_url = address_map[upload_info["url"]]
                    else:
                        raise BackendClientError(
                            "Overriding storage proxy addresses are given, "
                            "but no url matches with any of them.\n",
                        )
                params = {"token": upload_info["token"]}
                if dst_dir is not None:
                    params["dst_dir"] = dst_dir
                upload_url = URL(overriden_url).with_query(params)
            tus_client = client.TusClient()
            if basedir:
                input_file = open(base_path / file_path, "rb")
            else:
                input_file = open(str(Path(file_path).relative_to(base_path)), "rb")
            print(f"Uploading {base_path / file_path} via {upload_info['url']} ...")
            # TODO: refactor out the progress bar
            uploader = tus_client.async_uploader(
                file_stream=input_file,
                url=upload_url,
                upload_checksum=False,
                chunk_size=chunk_size,
            )
            await uploader.upload()
            input_file.close()

    async def _upload_recursively(
        self,
        source: Sequence[Path],
        basedir: Union[str, Path] = None,
        dst_dir: Union[str, Path] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        address_map: Optional[Mapping[str, str]] = None,
    ) -> None:
        dir_list: list[Path] = []
        file_list: list[Path] = []
        base_path = Path.cwd() if basedir is None else Path(basedir).resolve()
        for path in source:
            if path.is_file():
                file_list.append(path)
            else:
                await self._mkdir([path.relative_to(base_path)])
                dir_list.append(path)
        await self._upload_files(file_list, basedir, dst_dir, chunk_size, address_map)
        for dir in dir_list:
            await self._upload_recursively(
                list(dir.glob("*")), basedir, dst_dir, chunk_size, address_map
            )

    @api_function
    async def upload(
        self,
        sources: Sequence[Union[str, Path]],
        *,
        basedir: Union[str, Path] = None,
        recursive: bool = False,
        dst_dir: Union[str, Path] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        address_map: Optional[Mapping[str, str]] = None,
        show_progress: bool = False,
    ) -> None:
        if basedir:
            src_paths = [basedir / Path(src) for src in sources]
        else:
            src_paths = [Path(src).resolve() for src in sources]
        if recursive:
            await self._upload_recursively(src_paths, basedir, dst_dir, chunk_size, address_map)
        else:
            await self._upload_files(src_paths, basedir, dst_dir, chunk_size, address_map)

    async def _mkdir(
        self,
        path: str | Path | list_[str | Path],
        parents: Optional[bool] = False,
        exist_ok: Optional[bool] = False,
    ) -> ResultSet:
        rqst = Request("POST", "/folders/{}/mkdir".format(self.name))
        rqst.set_json({
            "path": path,
            "parents": parents,
            "exist_ok": exist_ok,
        })
        async with rqst.fetch() as resp:
            reply = await resp.json()
            return reply["results"]

    @api_function
    async def mkdir(
        self,
        path: str | Path | list_[str | Path],
        parents: Optional[bool] = False,
        exist_ok: Optional[bool] = False,
    ) -> ResultSet:
        return await self._mkdir(path, parents, exist_ok)

    @api_function
    async def rename_file(self, target_path: str, new_name: str):
        rqst = Request("POST", "/folders/{}/rename-file".format(self.name))
        rqst.set_json({
            "target_path": target_path,
            "new_name": new_name,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def move_file(self, src_path: str, dst_path: str):
        rqst = Request("POST", "/folders/{}/move-file".format(self.name))
        rqst.set_json({
            "src": src_path,
            "dst": dst_path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete_files(self, files: Sequence[Union[str, Path]], recursive: bool = False):
        rqst = Request("DELETE", "/folders/{}/delete-files".format(self.name))
        rqst.set_json({
            "files": files,
            "recursive": recursive,
        })
        async with rqst.fetch() as resp:
            return await resp.text()

    @api_function
    async def list_files(self, path: Union[str, Path] = "."):
        rqst = Request("GET", "/folders/{}/files".format(self.name))
        rqst.set_json({
            "path": path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def invite(self, perm: str, emails: Sequence[str]):
        rqst = Request("POST", "/folders/{}/invite".format(self.name))
        rqst.set_json({
            "perm": perm,
            "user_ids": emails,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def invitations(cls):
        rqst = Request("GET", "/folders/invitations/list")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def accept_invitation(cls, inv_id: str):
        rqst = Request("POST", "/folders/invitations/accept")
        rqst.set_json({"inv_id": inv_id})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete_invitation(cls, inv_id: str):
        rqst = Request("DELETE", "/folders/invitations/delete")
        rqst.set_json({"inv_id": inv_id})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_fstab_contents(cls, agent_id=None):
        rqst = Request("GET", "/folders/_/fstab")
        rqst.set_json({
            "agent_id": agent_id,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_performance_metric(cls, folder_host: str):
        rqst = Request("GET", "/folders/_/perf-metric")
        rqst.set_json({
            "folder_host": folder_host,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_mounts(cls):
        rqst = Request("GET", "/folders/_/mounts")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def mount_host(cls, name: str, fs_location: str, options=None, edit_fstab: bool = False):
        rqst = Request("POST", "/folders/_/mounts")
        rqst.set_json({
            "name": name,
            "fs_location": fs_location,
            "options": options,
            "edit_fstab": edit_fstab,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def umount_host(cls, name: str, edit_fstab: bool = False):
        rqst = Request("DELETE", "/folders/_/mounts")
        rqst.set_json({
            "name": name,
            "edit_fstab": edit_fstab,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def share(self, perm: str, emails: Sequence[str]):
        rqst = Request("POST", "/folders/{}/share".format(self.name))
        rqst.set_json({
            "permission": perm,
            "emails": emails,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def unshare(self, emails: Sequence[str]):
        rqst = Request("DELETE", "/folders/{}/unshare".format(self.name))
        rqst.set_json({
            "emails": emails,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def leave(self, shared_user_uuid=None):
        rqst = Request("POST", "/folders/{}/leave".format(self.name))
        rqst.set_json({"shared_user_uuid": shared_user_uuid})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def clone(
        self,
        target_name: str,
        target_host: str = None,
        usage_mode: str = "general",
        permission: str = "rw",
    ):
        rqst = Request("POST", "/folders/{}/clone".format(self.name))
        rqst.set_json({
            "target_name": target_name,
            "target_host": target_host,
            "usage_mode": usage_mode,
            "permission": permission,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def update_options(self, name: str, permission: str = None, cloneable: bool = None):
        rqst = Request("POST", "/folders/{}/update-options".format(self.name))
        rqst.set_json({
            "cloneable": cloneable,
            "permission": permission,
        })
        async with rqst.fetch() as resp:
            return await resp.text()

    @api_function
    @classmethod
    async def list_shared_vfolders(cls):
        rqst = Request("GET", "folders/_/shared")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def shared_vfolder_info(cls, vfolder_id: str):
        rqst = Request("GET", "folders/_/shared")
        rqst.set_json({"vfolder_id": vfolder_id})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def update_shared_vfolder(cls, vfolder: str, user: str, perm: str = None):
        rqst = Request("POST", "/folders/_/shared")
        rqst.set_json({
            "vfolder": vfolder,
            "user": user,
            "perm": perm,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def change_vfolder_ownership(cls, vfolder: str, user_email: str):
        rqst = Request("POST", "/folders/_/change-ownership")
        rqst.set_json({
            "vfolder": vfolder,
            "user_email": user_email,
        })
        async with rqst.fetch() as resp:
            return await resp.json()
