"""
Client-facing API
"""

import asyncio
import json
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Any, Final, Mapping, MutableMapping, cast

import aiohttp_cors
import janus
import trafaret as t
import zipstream
from aiohttp import hdrs, web

from ai.backend.common import validators as tx
from ai.backend.common.files import AsyncFileWriter
from ai.backend.common.logging import BraceStyleAdapter

from ..abc import AbstractVolume
from ..context import Context
from ..exception import InvalidAPIParameters
from ..types import SENTINEL
from ..utils import CheckParamSource, check_params

log = BraceStyleAdapter(logging.getLogger(__name__))

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8


download_token_data_iv = t.Dict(
    {
        t.Key("op"): t.Atom("download"),
        t.Key("volume"): t.String,
        t.Key("vfid"): tx.UUID,
        t.Key("relpath"): t.String,
        t.Key("archive", default=False): t.Bool,
        t.Key("unmanaged_path", default=None): t.Null | t.String,
    },
).allow_extra(
    "*",
)  # allow JWT-intrinsic keys

upload_token_data_iv = t.Dict(
    {
        t.Key("op"): t.Atom("upload"),
        t.Key("volume"): t.String,
        t.Key("vfid"): tx.UUID,
        t.Key("relpath"): t.String,
        t.Key("session"): t.String,
        t.Key("size"): t.Int,
    },
).allow_extra(
    "*",
)  # allow JWT-intrinsic keys


async def download(request: web.Request) -> web.StreamResponse:
    ctx: Context = request.app["ctx"]
    secret = ctx.local_config["storage-proxy"]["secret"]
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("token"): tx.JsonWebToken(
                    secret=secret,
                    inner_iv=download_token_data_iv,
                ),
                t.Key("archive", default=False): t.ToBool,
                t.Key("no_cache", default=False): t.ToBool,
            },
        ),
        read_from=CheckParamSource.QUERY,
    ) as params:
        async with ctx.get_volume(params["token"]["volume"]) as volume:
            token_data = params["token"]
            if token_data["unmanaged_path"] is not None:
                vfpath = Path(token_data["unmanaged_path"])
            else:
                vfpath = volume.mangle_vfpath(token_data["vfid"])
            try:
                file_path = (vfpath / token_data["relpath"]).resolve()
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
                return web.Response(
                    status=200,
                    headers={
                        hdrs.ACCEPT_RANGES: "bytes",
                        hdrs.CONTENT_LENGTH: str(file_path.stat().st_size),
                    },
                )
    ascii_filename = (
        file_path.name.encode("ascii", errors="ignore")
        .decode("ascii")
        .replace('"', r"\"")
    )
    encoded_filename = urllib.parse.quote(file_path.name, encoding="utf-8")
    headers = {
        hdrs.CONTENT_TYPE: "application/octet-stream",
        hdrs.CONTENT_DISPOSITION: " ".join(
            [
                "attachment;" f'filename="{ascii_filename}";',  # RFC-2616 sec2.2
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
    zip_filename: str = None,
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
        zip_filename.encode("ascii", errors="ignore")
        .decode("ascii")
        .replace('"', r"\"")
    )
    encoded_filename = urllib.parse.quote(zip_filename, encoding="utf-8")
    response = web.StreamResponse(
        headers={
            hdrs.CONTENT_TYPE: "application/zip",
            hdrs.CONTENT_DISPOSITION: " ".join(
                [
                    "attachment;" f'filename="{ascii_filename}";',  # RFC-2616 sec2.2
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
    ctx: Context = request.app["ctx"]
    secret = ctx.local_config["storage-proxy"]["secret"]
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("token"): tx.JsonWebToken(
                    secret=secret,
                    inner_iv=upload_token_data_iv,
                ),
            },
        ),
        read_from=CheckParamSource.QUERY,
    ) as params:
        token_data = params["token"]
        async with ctx.get_volume(token_data["volume"]) as volume:
            headers = await prepare_tus_session_headers(request, token_data, volume)
    return web.Response(headers=headers)


async def tus_upload_part(request: web.Request) -> web.Response:
    """
    Perform the chunk upload.
    """
    ctx: Context = request.app["ctx"]
    secret = ctx.local_config["storage-proxy"]["secret"]
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("token"): tx.JsonWebToken(
                    secret=secret,
                    inner_iv=upload_token_data_iv,
                ),
            },
        ),
        read_from=CheckParamSource.QUERY,
    ) as params:
        token_data = params["token"]
        async with ctx.get_volume(token_data["volume"]) as volume:
            headers = await prepare_tus_session_headers(request, token_data, volume)
            vfpath = volume.mangle_vfpath(token_data["vfid"])
            upload_temp_path = vfpath / ".upload" / token_data["session"]

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
                target_path = vfpath / token_data["relpath"]
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
    ctx: Context = request.app["ctx"]
    headers = {}
    headers["Access-Control-Allow-Origin"] = "*"
    headers[
        "Access-Control-Allow-Headers"
    ] = "Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type"
    headers[
        "Access-Control-Expose-Headers"
    ] = "Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type"
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
    headers[
        "Access-Control-Allow-Headers"
    ] = "Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type"
    headers[
        "Access-Control-Expose-Headers"
    ] = "Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type"
    headers["Access-Control-Allow-Methods"] = "*"
    headers["Cache-Control"] = "no-store"
    headers["Tus-Resumable"] = "1.0.0"
    headers["Upload-Offset"] = str(Path(upload_temp_path).stat().st_size)
    headers["Upload-Length"] = str(token_data["size"])
    return headers


async def init_client_app(ctx: Context) -> web.Application:
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
    r = cors.add(app.router.add_resource("/download"))
    r.add_route("GET", download)
    r = app.router.add_resource("/upload")  # tus handlers handle CORS by themselves
    r.add_route("OPTIONS", tus_options)
    r.add_route("HEAD", tus_check_session)
    r.add_route("PATCH", tus_upload_part)
    return app
