"""
Client-facing API
"""

from __future__ import annotations

import asyncio
import logging
import os
import urllib.parse
import uuid
from collections.abc import AsyncGenerator, Iterator, Mapping, MutableMapping
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Literal,
    TypedDict,
    cast,
)

import aiofiles
import aiofiles.os
import aiohttp_cors
import janus
import trafaret as t
import zipstream
from aiohttp import hdrs, web

from ai.backend.common import validators as tx
from ai.backend.common.api_handlers import (
    APIStreamResponse,
    QueryParam,
    stream_api_handler,
)
from ai.backend.common.dto.storage.request import (
    ArchiveDownloadQueryParams,
    ArchiveDownloadTokenData,
)
from ai.backend.common.json import dump_json_str
from ai.backend.common.metrics.http import build_api_metric_middleware
from ai.backend.common.middlewares.exception import general_exception_middleware
from ai.backend.common.typed_validators import PydanticJWTValidator
from ai.backend.common.types import BinarySize, VFolderID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage import __version__
from ai.backend.storage.dto.context import StorageRootCtx
from ai.backend.storage.errors import (
    InvalidAPIParameters,
    UploadOffsetMismatchError,
)
from ai.backend.storage.services.file_stream.zip import (
    ZipArchiveStreamReader,
)
from ai.backend.storage.types import SENTINEL
from ai.backend.storage.utils import (
    CheckParamSource,
    build_attachment_headers,
    check_params,
)

if TYPE_CHECKING:
    from aiohttp import StreamReader

    from ai.backend.storage.context import RootContext
    from ai.backend.storage.volumes.abc import AbstractVolume

from ai.backend.common.clients.valkey_client.valkey_tus import (
    TusSessionId,
    TusSessionNotFoundError,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8


async def _drain_into_upload_file(
    content: StreamReader,
    upload_temp_path: Path,
    start_offset: int,
    session_id: TusSessionId,
) -> int:
    """Truncate ``upload_temp_path`` to ``start_offset`` and append the body. Returns bytes written.

    First PATCH uses ``w+b`` (create or truncate to 0); continuations use
    ``r+b`` which refuses to create. A continuation with a missing staging
    file means it was wiped out of band (NFS GC, manual ``rm``, etc.) —
    re-creating would silently zero-pad the prefix via ``truncate`` and
    corrupt the upload. Surface it as a vanished session instead.
    """
    mode: Literal["w+b", "r+b"] = "w+b" if start_offset == 0 else "r+b"
    bytes_written = 0
    try:
        async with aiofiles.open(upload_temp_path, mode=mode) as f:
            # Discard any orphan tail bytes left by a prior crashed holder.
            await f.truncate(start_offset)
            await f.seek(start_offset)
            while not content.at_eof():
                chunk = await content.read(DEFAULT_CHUNK_SIZE)
                if not chunk:
                    continue
                await f.write(chunk)
                bytes_written += len(chunk)
            await f.flush()
            await asyncio.get_running_loop().run_in_executor(None, os.fsync, f.fileno())
    except FileNotFoundError as e:
        raise TusSessionNotFoundError(
            f"Upload session {session_id} staging file is missing at offset {start_offset}"
        ) from e
    return bytes_written


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
        AbstractAsyncContextManager[Params],
        check_params(
            request,
            t.Dict({}),
            read_from=CheckParamSource.QUERY,
        ),
    ) as _:
        return web.json_response(
            status=HTTPStatus.OK,
            data={
                "status": "ok",
                "type": "client-facing",
                "storage-proxy": __version__,
            },
        )


async def download(request: web.Request) -> web.StreamResponse:
    ctx: RootContext = request.app["ctx"]
    secret = ctx.local_config.storage_proxy.secret

    class Params(TypedDict):
        token: DownloadTokenData
        dst_dir: str
        archive: bool
        no_cache: bool

    async with (
        cast(
            AbstractAsyncContextManager[Params],
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
        ) as params,
        ctx.get_volume(params["token"]["volume"]) as volume,
    ):
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
            file_path.resolve().relative_to(vfpath)
            if not file_path.exists():
                raise FileNotFoundError
        except (ValueError, FileNotFoundError) as e:
            raise web.HTTPNotFound(
                body=dump_json_str(
                    {
                        "title": "File not found",
                        "type": "https://api.backend.ai/probs/storage/file-not-found",
                    },
                ),
                content_type="application/problem+json",
            ) from e
        if not file_path.is_file():
            if params["archive"]:
                # Download directory as an archive when archive param is set.
                return await download_directory_as_archive(request, file_path)
            raise InvalidAPIParameters(extra_msg="The file is not a regular file.")
        if request.method == "HEAD":
            ifrange: datetime | None = request.if_range
            mtime = file_path.stat().st_mtime
            last_mdt = datetime.fromtimestamp(mtime, tz=UTC)
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
                        f"{last_mdt.strftime('%a')}, {last_mdt.day} "
                        f"{last_mdt.strftime('%b')} {last_mdt.year} "
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

    def _iter2aiter(iter: Iterator[Any]) -> AsyncGenerator[Any, None]:
        """Iterable to async iterable"""

        def _consume(
            _loop: asyncio.AbstractEventLoop, iter: Iterator[Any], q: janus.SyncQueue[Any]
        ) -> None:
            for item in iter:
                q.put(item)
            q.put(SENTINEL)

        async def _aiter() -> AsyncGenerator[Any, None]:
            loop = asyncio.get_running_loop()
            q: janus.Queue[Any] = janus.Queue(maxsize=DEFAULT_INFLIGHT_CHUNKS)
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
    secret = ctx.local_config.storage_proxy.secret

    class Params(TypedDict):
        token: UploadTokenData
        dst_dir: str

    async with cast(
        AbstractAsyncContextManager[Params],
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
    secret = ctx.local_config.storage_proxy.secret

    class Params(TypedDict):
        token: UploadTokenData
        dst_dir: str

    async with cast(
        AbstractAsyncContextManager[Params],
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

            # TUS protocol requires Upload-Offset validation before appending data
            upload_offset_header = request.headers.get("Upload-Offset")
            if upload_offset_header is None:
                raise InvalidAPIParameters(
                    "Missing required Upload-Offset header for TUS PATCH request"
                )

            try:
                client_offset = int(upload_offset_header)
            except ValueError as e:
                raise InvalidAPIParameters(
                    f"Invalid Upload-Offset header value: {upload_offset_header}"
                ) from e

            await aiofiles.os.makedirs(upload_temp_path.parent, exist_ok=True)

            session_id = TusSessionId(token_data["session"])
            holder_token = f"{ctx.node_id}:{uuid.uuid4().hex}"
            actual_offset = await ctx.valkey_tus_client.try_load_offset(session_id, holder_token)
            if client_offset != actual_offset:
                # We hold the lease but the precondition fails — release it
                # before bailing so the next PATCH does not have to wait for
                # the TTL.
                await ctx.valkey_tus_client.release_lease(session_id, holder_token)
                raise UploadOffsetMismatchError(
                    f"Upload offset mismatch: expected {actual_offset}, got {client_offset}"
                )
            watcher_task = asyncio.create_task(
                ctx.valkey_tus_client.watch_lease(session_id, holder_token),
                name=f"tus-lease-watch-{session_id}",
            )
            try:
                bytes_written = await _drain_into_upload_file(
                    request.content, upload_temp_path, actual_offset, session_id
                )
            except BaseException:
                await ctx.valkey_tus_client.release_lease(session_id, holder_token)
                raise
            finally:
                watcher_task.cancel()
                try:
                    await watcher_task
                except asyncio.CancelledError:
                    pass
            new_offset = await ctx.valkey_tus_client.advance_offset(
                session_id, holder_token, bytes_written
            )

            headers["Upload-Offset"] = str(new_offset)
            if new_offset >= int(token_data["size"]):
                parent_dir = vfpath
                if (dst_dir := params["dst_dir"]) is not None:
                    parent_dir = vfpath / dst_dir
                target_path: Path = parent_dir / token_data["relpath"]
                if not target_path.parent.exists():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                upload_temp_path.rename(target_path)
                try:
                    await aiofiles.os.rmdir(upload_temp_path.parent)
                except OSError:
                    pass
    return web.Response(status=HTTPStatus.NO_CONTENT, headers=headers)


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
        int(BinarySize.from_str(ctx.local_config.storage_proxy.max_upload_size)),
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
        raise TusSessionNotFoundError(
            f"Upload session {token_data['session']} has no on-disk staging file"
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
    ctx: RootContext = request.app["ctx"]
    redis_offset = await ctx.valkey_tus_client.get_offset(TusSessionId(token_data["session"]))
    if redis_offset is None:
        raise TusSessionNotFoundError(
            f"Upload session {token_data['session']} is not registered or has expired"
        )
    headers["Upload-Offset"] = str(redis_offset)
    headers["Upload-Length"] = str(token_data["size"])
    return headers


class DownloadHandler:
    """Handler class for download operations following manager's api_handler pattern.

    Future refactoring: When StreamReader class is settled and if we decide to put
    Reader class in api_handler, we will refactor this to receive StreamReader as
    interface, which decouples handler logic from aiohttp web.Request/Response objects
    for better testability and separation of concerns.
    """

    def __init__(self, secret: str) -> None:
        self._jwt_validator = PydanticJWTValidator(secret=secret)

    @stream_api_handler
    async def download_archive(
        self,
        query: QueryParam[ArchiveDownloadQueryParams],
        ctx: StorageRootCtx,
    ) -> APIStreamResponse:
        """Stream multiple files/directories as a ZIP archive."""
        token_data = self._jwt_validator.validate(query.parsed.token, ArchiveDownloadTokenData)

        async with ctx.root_ctx.get_volume(token_data.volume) as volume:
            vfolder_root = volume.sanitize_vfpath(token_data.virtual_folder_id)
            sanitized: list[Path] = [
                (vfolder_root / relpath).resolve() for relpath in token_data.files
            ]
            for file_path, relpath in zip(sanitized, token_data.files, strict=True):
                if not file_path.is_relative_to(vfolder_root):
                    raise InvalidAPIParameters(
                        extra_msg=f"Path escapes vfolder boundary: {relpath}"
                    )
                if not file_path.exists():
                    raise web.HTTPNotFound(reason=f"File not found: {relpath}")

            reader = ZipArchiveStreamReader(vfolder_root)
            reader.add_entries(sanitized)

            filename = token_data.filename if token_data.filename is not None else reader.filename()
            headers = build_attachment_headers(filename, reader.content_type())
            return APIStreamResponse(body=reader, status=HTTPStatus.OK, headers=headers)


async def init_client_app(ctx: RootContext) -> web.Application:
    app = web.Application(
        middlewares=[
            general_exception_middleware,
            build_api_metric_middleware(ctx.metric_registry.api),
        ]
    )
    app["ctx"] = ctx

    # Initialize handler instances
    download_handler = DownloadHandler(secret=ctx.local_config.storage_proxy.secret)

    cors_options = {
        "*": aiohttp_cors.ResourceOptions(  # type: ignore[no-untyped-call]
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
    r = cors.add(app.router.add_resource("/download-archive"))
    r.add_route("GET", download_handler.download_archive)
    # tus handlers handle CORS by themselves
    r = app.router.add_resource("/upload")
    r.add_route("OPTIONS", tus_options)
    r.add_route("HEAD", tus_check_session)
    r.add_route("PATCH", tus_upload_part)

    return app
