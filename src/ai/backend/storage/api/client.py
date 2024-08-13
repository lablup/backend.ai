"""
Client-facing API
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    Final,
    Literal,
    Mapping,
    MutableMapping,
    TypedDict,
    cast,
)

import aiohttp_cors
import janus
import trafaret as t
import zipstream
from aiohttp import hdrs, web

from ai.backend.common import validators as tx
from ai.backend.common.files import AsyncFileWriter
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import VFolderID

from .. import __version__
from ..exception import InvalidAPIParameters
from ..types import SENTINEL
from ..utils import CheckParamSource, check_params

if TYPE_CHECKING:
    from ..abc import AbstractVolume
    from ..context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8


class DownloadTokenData(TypedDict):
    op: Literal["download"]
    volume: str
    vfid: VFolderID
    relpath: str
    archive: bool
    unmanaged_path: str | None


download_token_data_iv = t.Dict(
    {
        t.Key("op"): t.Atom("download"),
        t.Key("volume"): t.String,
        t.Key("vfid"): tx.VFolderID,
        t.Key("relpath"): t.String,
        t.Key("archive", default=False): t.Bool,
        t.Key("unmanaged_path", default=None): t.Null | t.String,
    },
).allow_extra(
    "*",
)  # allow JWT-intrinsic keys


class UploadTokenData(TypedDict):
    op: Literal["upload"]
    volume: str
    vfid: VFolderID
    relpath: str
    session: str
    size: int


upload_token_data_iv = t.Dict(
    {
        t.Key("op"): t.Atom("upload"),
        t.Key("volume"): t.String,
        t.Key("vfid"): tx.VFolderID,
        t.Key("relpath"): t.String,
        t.Key("session"): t.String,
        t.Key("size"): t.Int,
    },
).allow_extra(
    "*",
)  # allow JWT-intrinsic keys


async def check_status(request: web.Request) -> web.StreamResponse:
    class Params(TypedDict):
        pass

    async with cast(
        AsyncContextManager[Params],
        check_params(
            request,
            t.Dict({}),
            read_from=CheckParamSource.QUERY,
        ),
    ) as _:
        return web.json_response(
            status=200,
            data={
                "status": "ok",
                "type": "client-facing",
                "storage-proxy": __version__,
            },
        )


async def download(request: web.Request) -> web.StreamResponse:
    ctx: RootContext = request.app["ctx"]
    secret = ctx.local_config["storage-proxy"]["secret"]

    class Params(TypedDict):
        token: DownloadTokenData
        dst_dir: str
        archive: bool
        no_cache: bool

    async with cast(
        AsyncContextManager[Params],
        check_params(
            request,
            t.Dict(
                {
                    t.Key("token"): tx.JsonWebToken(
                        secret=secret,
                        inner_iv=download_token_data_iv,
                    ),
                    t.Key("dst_dir", default=None): t.Null | t.String,
                    t.Key("archive", default=False): t.ToBool,
                    t.Key("no_cache", default=False): t.ToBool,
                },
            ),
            read_from=CheckParamSource.QUERY,
        ),
    ) as params:
        async with ctx.get_volume(params["token"]["volume"]) as volume:
            token_data = params["token"]
            if token_data["unmanaged_path"] is not None:
                vfpath = Path(token_data["unmanaged_path"])
            else:
                vfpath = volume.mangle_vfpath(token_data["vfid"])
            try:
                parent_dir = vfpath
                if (dst_dir := params["dst_dir"]) is not None:
                    parent_dir = vfpath / dst_dir
                file_path = parent_dir / token_data["relpath"]
                file_path.relative_to(vfpath)
                if not file_path.exists():
                    raise FileNotFoundError
            except (ValueError, FileNotFoundError):
                raise web.HTTPNotFound(
                    body=json.dumps(
                        {
                            "title": "File not found",
                            "type": "https://api.backend.ai/probs/storage/file-not-found",
                        },
                    ),
                    content_type="application/problem+json",
                )
            if not file_path.is_file():
                if params["archive"]:
                    # Download directory as an archive when archive param is set.
                    return await download_directory_as_archive(request, file_path)
                else:
                    raise InvalidAPIParameters("The file is not a regular file.")
            if request.method == "HEAD":
                ifrange: datetime | None = request.if_range
                mtime = os.stat(file_path).st_mtime
                last_mdt = datetime.fromtimestamp(mtime)
                resp_status = 200
                if ifrange is not None and mtime <= ifrange.timestamp():
                    # Return partial content.
                    resp_status = 206
                return web.Response(
                    status=resp_status,
                    headers={
                        hdrs.ACCEPT_RANGES: "bytes",
                        hdrs.CONTENT_LENGTH: str(file_path.stat().st_size),
                        hdrs.LAST_MODIFIED: (
                            f'{last_mdt.strftime("%a")}, {last_mdt.day} '
                            f'{last_mdt.strftime("%b")} {last_mdt.year} '
                            f"{last_mdt.hour}:{last_mdt.minute}:{last_mdt.second} GMT"
                        ),
                    },
                )
    ascii_filename = (
        file_path.name.encode("ascii", errors="ignore").decode("ascii").replace('"', r"\"")
    )
    encoded_filename = urllib.parse.quote(file_path.name, encoding="utf-8")
    headers = {
        hdrs.CONTENT_TYPE: "application/octet-stream",
        hdrs.CONTENT_DISPOSITION: " ".join(
            [
                f'attachment;filename="{ascii_filename}";',  # RFC-2616 sec2.2
                f"filename*=UTF-8''{encoded_filename}",  # RFC-5987
            ],
        ),
    }
    if params["no_cache"]:
        headers[hdrs.CACHE_CONTROL] = "no-store"
    return web.FileResponse(file_path, headers=cast(Mapping[str, str], headers))


async def download_directory_as_archive(
    request: web.Request,
    file_path: Path,
    zip_filename: str | None = None,
) -> web.StreamResponse:
    """
    Serve a directory as a zip archive on the fly.
    """

    def _iter2aiter(iter):
        """Iterable to async iterable"""

        def _consume(loop, iter, q):
            for item in iter:
                q.put(item)
            q.put(SENTINEL)

        async def _aiter():
            loop = asyncio.get_running_loop()
            q = janus.Queue(maxsize=DEFAULT_INFLIGHT_CHUNKS)
            try:
                fut = loop.run_in_executor(None, lambda: _consume(loop, iter, q.sync_q))
                while True:
                    item = await q.async_q.get()
                    if item is SENTINEL:
                        break
                    yield item
                    q.async_q.task_done()
                await fut
            finally:
                q.close()
                await q.wait_closed()

        return _aiter()

    if zip_filename is None:
        zip_filename = file_path.name + ".zip"
    zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)
    async for root, dirs, files in _iter2aiter(os.walk(file_path)):
        for file in files:
            zf.write(Path(root) / file, Path(root).relative_to(file_path) / file)
        if len(dirs) == 0 and len(files) == 0:
            # Include an empty directory in the archive as well.
            zf.write(root, Path(root).relative_to(file_path))
    ascii_filename = (
        zip_filename.encode("ascii", errors="ignore").decode("ascii").replace('"', r"\"")
    )
    encoded_filename = urllib.parse.quote(zip_filename, encoding="utf-8")
    response = web.StreamResponse(
        headers={
            hdrs.CONTENT_TYPE: "application/zip",
            hdrs.CONTENT_DISPOSITION: " ".join(
                [
                    f'attachment;filename="{ascii_filename}";',  # RFC-2616 sec2.2
                    f"filename*=UTF-8''{encoded_filename}",  # RFC-5987
                ],
            ),
        },
    )
    await response.prepare(request)
    async for chunk in _iter2aiter(zf):
        await response.write(chunk)
    return response


async def tus_check_session(request: web.Request) -> web.Response:
    """
    Check the availability of an upload session.
    """
    ctx: RootContext = request.app["ctx"]
    secret = ctx.local_config["storage-proxy"]["secret"]

    class Params(TypedDict):
        token: UploadTokenData
        dst_dir: str

    async with cast(
        AsyncContextManager[Params],
        check_params(
            request,
            t.Dict(
                {
                    t.Key("token"): tx.JsonWebToken(
                        secret=secret,
                        inner_iv=upload_token_data_iv,
                    ),
                    t.Key("dst_dir", default=None): t.Null | t.String,
                },
            ),
            read_from=CheckParamSource.QUERY,
        ),
    ) as params:
        token_data = params["token"]
        async with ctx.get_volume(token_data["volume"]) as volume:
            headers = await prepare_tus_session_headers(request, token_data, volume)
    return web.Response(headers=headers)


async def tus_upload_part(request: web.Request) -> web.Response:
    """
    Perform the chunk upload.
    """
    ctx: RootContext = request.app["ctx"]
    secret = ctx.local_config["storage-proxy"]["secret"]

    class Params(TypedDict):
        token: UploadTokenData
        dst_dir: str

    async with cast(
        AsyncContextManager[Params],
        check_params(
            request,
            t.Dict(
                {
                    t.Key("token"): tx.JsonWebToken(
                        secret=secret,
                        inner_iv=upload_token_data_iv,
                    ),
                    t.Key("dst_dir", default=None): t.Null | t.String,
                },
            ),
            read_from=CheckParamSource.QUERY,
        ),
    ) as params:
        token_data = params["token"]
        async with ctx.get_volume(token_data["volume"]) as volume:
            headers = await prepare_tus_session_headers(request, token_data, volume)
            vfpath = volume.mangle_vfpath(token_data["vfid"])
            upload_temp_path: Path = vfpath / ".upload" / token_data["session"]

            async with AsyncFileWriter(
                target_filename=upload_temp_path,
                access_mode="ab",
                max_chunks=DEFAULT_INFLIGHT_CHUNKS,
            ) as writer:
                while not request.content.at_eof():
                    chunk = await request.content.read(DEFAULT_CHUNK_SIZE)
                    await writer.write(chunk)

            current_size = Path(upload_temp_path).stat().st_size
            if current_size >= int(token_data["size"]):
                parent_dir = vfpath
                if (dst_dir := params["dst_dir"]) is not None:
                    parent_dir = vfpath / dst_dir
                target_path: Path = parent_dir / token_data["relpath"]
                if not target_path.parent.exists():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                upload_temp_path.rename(target_path)
                try:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: upload_temp_path.parent.rmdir(),
                    )
                except OSError:
                    pass
            headers["Upload-Offset"] = str(current_size)
    return web.Response(status=204, headers=headers)


async def tus_options(request: web.Request) -> web.Response:
    """
    Let clients discover the supported features of our tus.io server-side implementation.
    """
    ctx: RootContext = request.app["ctx"]
    headers = {}
    headers["Access-Control-Allow-Origin"] = "*"
    headers["Access-Control-Allow-Headers"] = (
        "Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type"
    )
    headers["Access-Control-Expose-Headers"] = (
        "Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type"
    )
    headers["Access-Control-Allow-Methods"] = "*"
    headers["Tus-Resumable"] = "1.0.0"
    headers["Tus-Version"] = "1.0.0"
    headers["Tus-Max-Size"] = str(
        int(ctx.local_config["storage-proxy"]["max-upload-size"]),
    )
    headers["X-Content-Type-Options"] = "nosniff"
    return web.Response(headers=headers)


async def prepare_tus_session_headers(
    request: web.Request,
    token_data: Mapping[str, Any],
    volume: AbstractVolume,
) -> MutableMapping[str, str]:
    vfpath = volume.mangle_vfpath(token_data["vfid"])
    upload_temp_path = vfpath / ".upload" / token_data["session"]
    if not Path(upload_temp_path).exists():
        raise web.HTTPNotFound(
            body=json.dumps(
                {
                    "title": "No such upload session",
                    "type": "https://api.backend.ai/probs/storage/no-such-upload-session",
                },
            ),
            content_type="application/problem+json",
        )
    headers = {}
    headers["Access-Control-Allow-Origin"] = "*"
    headers["Access-Control-Allow-Headers"] = (
        "Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type"
    )
    headers["Access-Control-Expose-Headers"] = (
        "Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type"
    )
    headers["Access-Control-Allow-Methods"] = "*"
    headers["Cache-Control"] = "no-store"
    headers["Tus-Resumable"] = "1.0.0"
    headers["Upload-Offset"] = str(Path(upload_temp_path).stat().st_size)
    headers["Upload-Length"] = str(token_data["size"])
    return headers


async def init_client_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            allow_methods="*",
            expose_headers="*",
            allow_headers="*",
        ),
    }
    cors = aiohttp_cors.setup(app, defaults=cors_options)
    r = cors.add(app.router.add_resource("/"))
    r.add_route("GET", check_status)
    r = cors.add(app.router.add_resource("/download"))
    r.add_route("GET", download)
    r = app.router.add_resource("/upload")  # tus handlers handle CORS by themselves
    r.add_route("OPTIONS", tus_options)
    r.add_route("HEAD", tus_check_session)
    r.add_route("PATCH", tus_upload_part)

    return app
