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
from ai.backend.common.files import AsyncFileWriter
from ai.backend.common.json import dump_json_str
from ai.backend.common.metrics.http import build_api_metric_middleware
from ai.backend.common.middlewares.exception import general_exception_middleware
from ai.backend.common.typed_validators import PydanticJWTValidator
from ai.backend.common.types import BinarySize, VFolderID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage import __version__
from ai.backend.storage.dto.context import StorageRootCtx
from ai.backend.storage.errors import InvalidAPIParameters, UploadOffsetMismatchError
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
    from ai.backend.storage.context import RootContext
    from ai.backend.storage.volumes.abc import AbstractVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8


def _fsync_file(path: Path) -> None:
    """Synchronously flush the chunk file's contents to durable storage.

    Called between the file append and the Valkey ``INCRBY`` so that a crash
    immediately after the write but before the offset commit cannot leave the
    next PATCH appending on top of half-flushed bytes.
    """
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _commit_staging(upload_temp_path: Path, staging_path: Path, known_good_offset: int) -> None:
    """Atomically commit ``staging_path`` content onto ``upload_temp_path``.

    Performed inside the per-session Sokovan lease. ``known_good_offset`` is
    the Valkey-known committed offset — the file is unconditionally truncated
    to that length before append, which both creates the file if missing (via
    ``O_CREAT``) and discards any orphan bytes left behind by a prior holder
    that crashed mid-write (no ``stat()`` needed; we always reset the length
    to a value Valkey vouches for). The staging bytes are then written and
    fsync'd so the durability claim is true before the caller's ``INCRBY``.
    """
    chunk_size = 1024 * 1024  # 1 MiB local→NFS copy buffer
    dst_fd = os.open(
        str(upload_temp_path),
        os.O_WRONLY | os.O_CREAT,
        0o644,
    )
    try:
        os.ftruncate(dst_fd, known_good_offset)
        os.lseek(dst_fd, known_good_offset, os.SEEK_SET)
        with Path(staging_path).open("rb") as src:
            while True:
                buf = src.read(chunk_size)
                if not buf:
                    break
                view = memoryview(buf)
                while view:
                    n = os.write(dst_fd, view)
                    view = view[n:]
        os.fsync(dst_fd)
    finally:
        os.close(dst_fd)


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

            loop = asyncio.get_running_loop()

            # Phase 1 (outside the lock): drain the request body into a
            # per-attempt staging file. Holding the Sokovan lease for the
            # network read would balloon the critical section to the full
            # chunk transfer time (seconds for 100MB+ chunks); keeping it
            # outside means the lock only covers fast local commit ops.
            # ``staged_bytes`` is tracked here — never via ``stat()`` —
            # so the offset accounting is independent of NFS attribute
            # cache (the very thing this whole fix exists to escape).
            upload_dir = upload_temp_path.parent
            await loop.run_in_executor(None, lambda: upload_dir.mkdir(parents=True, exist_ok=True))
            staging_path = upload_dir / (f"{token_data['session']}.staging.{uuid.uuid4().hex}")
            staged_bytes = 0
            try:
                async with AsyncFileWriter(
                    target_filename=staging_path,
                    access_mode="wb",
                    max_chunks=DEFAULT_INFLIGHT_CHUNKS,
                ) as writer:
                    while not request.content.at_eof():
                        chunk = await request.content.read(DEFAULT_CHUNK_SIZE)
                        await writer.write(chunk)
                        staged_bytes += len(chunk)
                await loop.run_in_executor(None, _fsync_file, staging_path)

                # Phase 2 (under the lock): commit staging → upload file →
                # Valkey, all serialized against other replicas via the
                # Sokovan-style TTL lease.
                holder_token = f"{ctx.node_id}:{uuid.uuid4().hex}"
                acquired = await ctx.valkey_tus_client.acquire_lock(
                    token_data["session"], holder_token
                )
                if not acquired:
                    # Another replica is mid-PATCH for this session — under
                    # spec-compliant sequential clients this can only mean
                    # a timeout-induced concurrent retry. 409 lets the
                    # client HEAD and re-sync to the canonical offset.
                    raise UploadOffsetMismatchError("session is being written by another replica")
                try:
                    actual_offset = await ctx.valkey_tus_client.get_offset(token_data["session"])
                    if actual_offset is None:
                        raise web.HTTPNotFound(
                            body=dump_json_str(
                                {
                                    "title": "No such upload session",
                                    "type": "https://api.backend.ai/probs/storage/no-such-upload-session",
                                },
                            ),
                            content_type="application/problem+json",
                        )
                    if client_offset != actual_offset:
                        raise UploadOffsetMismatchError(
                            f"Upload offset mismatch: expected {actual_offset}, got {client_offset}"
                        )

                    # Single fd: open with O_CREAT (handles first PATCH of a
                    # fresh session), ftruncate to the Valkey-known committed
                    # offset (discards any orphan bytes from a prior crashed
                    # holder — no ``stat()`` needed because we always reset
                    # the length to a known-good value), seek to the end,
                    # write staging payload, fsync, close.
                    await loop.run_in_executor(
                        None,
                        _commit_staging,
                        upload_temp_path,
                        staging_path,
                        actual_offset,
                    )
                    new_offset = await ctx.valkey_tus_client.advance_offset(
                        token_data["session"], length=staged_bytes
                    )
                finally:
                    await ctx.valkey_tus_client.release_lock(token_data["session"], holder_token)
            finally:
                # Always remove the staging file. Crash-leftover stagings are
                # garbage-collected separately by directory mtime sweeps.
                try:
                    await loop.run_in_executor(
                        None,
                        staging_path.unlink,
                        True,  # missing_ok=True
                    )
                except OSError:
                    pass

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
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: upload_temp_path.parent.rmdir(),
                    )
                except OSError:
                    pass
            headers["Upload-Offset"] = str(new_offset)
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
        raise web.HTTPNotFound(
            body=dump_json_str(
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
    # Read the offset from the shared TUS coordinator (BA-3974 fix). Falling
    # back to ``stat().st_size`` would re-introduce the NFS-attribute-cache
    # race that this coordinator exists to bypass.
    ctx: RootContext = request.app["ctx"]
    redis_offset = await ctx.valkey_tus_client.get_offset(token_data["session"])
    if redis_offset is None:
        # Session was never registered or its TTL elapsed.
        raise web.HTTPNotFound(
            body=dump_json_str(
                {
                    "title": "No such upload session",
                    "type": "https://api.backend.ai/probs/storage/no-such-upload-session",
                },
            ),
            content_type="application/problem+json",
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
