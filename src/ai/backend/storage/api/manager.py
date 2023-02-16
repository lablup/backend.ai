"""
Manager-facing API
"""

import json
import logging
from contextlib import contextmanager as ctxmgr
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Iterator, List
from uuid import UUID

import attr
import jwt
import trafaret as t
from aiohttp import hdrs, web

from ai.backend.common import validators as tx
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.storage.exception import ExecutionError

from ..abc import AbstractVolume
from ..context import Context
from ..exception import InvalidSubpathError, VFolderNotFoundError
from ..types import VFolderCreationOptions
from ..utils import check_params, log_manager_api_entry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@web.middleware
async def token_auth_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    token = request.headers.get("X-BackendAI-Storage-Auth-Token", None)
    if not token:
        raise web.HTTPForbidden()
    ctx: Context = request.app["ctx"]
    if token != ctx.local_config["api"]["manager"]["secret"]:
        raise web.HTTPForbidden()
    return await handler(request)


async def get_status(request: web.Request) -> web.Response:
    async with check_params(request, None) as params:
        await log_manager_api_entry(log, "get_status", params)
        return web.json_response(
            {
                "status": "ok",
            },
        )


@ctxmgr
def handle_fs_errors(
    volume: AbstractVolume,
    vfid: UUID,
) -> Iterator[None]:
    try:
        yield
    except OSError as e:
        related_paths = []
        msg = str(e) if e.strerror is None else e.strerror
        if e.filename:
            related_paths.append(str(volume.strip_vfpath(vfid, Path(e.filename))))
        if e.filename2:
            related_paths.append(str(volume.strip_vfpath(vfid, Path(e.filename2))))
        raise web.HTTPBadRequest(
            body=json.dumps(
                {
                    "msg": msg,
                    "errno": e.errno,
                    "paths": related_paths,
                },
            ),
            content_type="application/json",
        )


async def get_volumes(request: web.Request) -> web.Response:
    async def _get_caps(ctx: Context, volume_name: str) -> List[str]:
        async with ctx.get_volume(volume_name) as volume:
            return [*await volume.get_capabilities()]

    async with check_params(request, None) as params:
        await log_manager_api_entry(log, "get_volumes", params)
        ctx: Context = request.app["ctx"]
        volumes = ctx.list_volumes()
        return web.json_response(
            {
                "volumes": [
                    {
                        "name": name,
                        "backend": info.backend,
                        "path": str(info.path),
                        "fsprefix": str(info.fsprefix),
                        "capabilities": await _get_caps(ctx, name),
                    }
                    for name, info in volumes.items()
                ],
            },
        )


async def get_hwinfo(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "get_hwinfo", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            data = await volume.get_hwinfo()
            return web.json_response(data)


async def create_vfolder(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("options", default=None): t.Null | VFolderCreationOptions.as_trafaret(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "create_vfolder", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            obj_opts = VFolderCreationOptions.as_object(params["options"])
            await volume.create_vfolder(params["vfid"], obj_opts)
            return web.Response(status=204)


async def delete_vfolder(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "delete_vfolder", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            await volume.delete_vfolder(params["vfid"])
            return web.Response(status=204)


async def clone_vfolder(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("src_volume"): t.String(),
                t.Key("src_vfid"): tx.UUID(),
                t.Key("dst_volume"): t.String(),
                t.Key("dst_vfid"): tx.UUID(),
                t.Key("options", default=None): t.Null | VFolderCreationOptions.as_trafaret(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "clone_vfolder", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["src_volume"]) as src_volume:
            async with ctx.get_volume(params["dst_volume"]) as dst_volume:
                await src_volume.clone_vfolder(
                    params["src_vfid"],
                    dst_volume,
                    params["dst_vfid"],
                )
        return web.Response(status=204)


async def get_vfolder_mount(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("subpath", default="."): t.String(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "get_container_mount", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            try:
                mount_path = await volume.get_vfolder_mount(
                    params["vfid"],
                    params["subpath"],
                )
            except VFolderNotFoundError:
                raise web.HTTPBadRequest(
                    body=json.dumps(
                        {
                            "msg": "VFolder not found",
                            "vfid": str(params["vfid"]),
                        },
                    ),
                    content_type="application/json",
                )
            except InvalidSubpathError as e:
                raise web.HTTPBadRequest(
                    body=json.dumps(
                        {
                            "msg": "Invalid vfolder subpath",
                            "vfid": str(params["vfid"]),
                            "subpath": str(e.args[1]),
                        },
                    ),
                    content_type="application/json",
                )
            return web.json_response(
                {
                    "path": str(mount_path),
                },
            )


async def get_performance_metric(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "get_performance_metric", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            metric = await volume.get_performance_metric()
            return web.json_response(
                {
                    "metric": attr.asdict(metric),
                },
            )


async def fetch_file(request: web.Request) -> web.StreamResponse:
    """
    Direct file streaming API for internal use, such as retrieving
    task logs from a user vfolder ".logs".
    """
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("relpath"): tx.PurePath(relative_only=True),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "fetch_file", params)
        ctx: Context = request.app["ctx"]
        response = web.StreamResponse(status=200)
        response.headers[hdrs.CONTENT_TYPE] = "application/octet-stream"
        try:
            prepared = False
            async with ctx.get_volume(params["volume"]) as volume:
                with handle_fs_errors(volume, params["vfid"]):
                    async for chunk in volume.read_file(
                        params["vfid"],
                        params["relpath"],
                    ):
                        if not chunk:
                            return response
                        if not prepared:
                            await response.prepare(request)
                            prepared = True
                        await response.write(chunk)
        except FileNotFoundError:
            response = web.Response(status=404, reason="Log data not found")
        finally:
            if prepared:
                await response.write_eof()
            return response


async def get_metadata(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "get_metadata", params)
        return web.json_response(
            {
                "status": "ok",
            },
        )


async def set_metadata(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("payload"): t.Bytes(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "set_metadata", params)
        return web.json_response(
            {
                "status": "ok",
            },
        )


async def get_vfolder_fs_usage(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "get_vfolder_fs_usage", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            fs_usage = await volume.get_fs_usage()
            return web.json_response(
                {
                    "capacity_bytes": fs_usage.capacity_bytes,
                    "used_bytes": fs_usage.used_bytes,
                },
            )


async def get_vfolder_usage(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
            },
        ),
    ) as params:
        try:
            await log_manager_api_entry(log, "get_vfolder_usage", params)
            ctx: Context = request.app["ctx"]
            async with ctx.get_volume(params["volume"]) as volume:
                usage = await volume.get_usage(params["vfid"])
                return web.json_response(
                    {
                        "file_count": usage.file_count,
                        "used_bytes": usage.used_bytes,
                    },
                )
        except ExecutionError:
            return web.Response(
                status=500,
                reason="Storage server is busy. Please try again",
            )


async def get_quota(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid", default=None): t.Null | tx.UUID,
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "get_quota", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            quota = await volume.get_quota(params["vfid"])
            return web.json_response(quota)


async def set_quota(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid", default=None): t.Null | tx.UUID,
                t.Key("size_bytes"): tx.BinarySize,
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "update_quota", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            await volume.set_quota(params["vfid"], params["size_bytes"])
            return web.Response(status=204)


async def mkdir(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("relpath"): tx.PurePath(relative_only=True),
                t.Key("parents", default=True): t.ToBool,
                t.Key("exist_ok", default=False): t.ToBool,
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "mkdir", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            with handle_fs_errors(volume, params["vfid"]):
                await volume.mkdir(
                    params["vfid"],
                    params["relpath"],
                    parents=params["parents"],
                    exist_ok=params["exist_ok"],
                )
        return web.Response(status=204)


async def list_files(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("relpath"): tx.PurePath(relative_only=True),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "list_files", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            with handle_fs_errors(volume, params["vfid"]):
                items = [
                    {
                        "name": item.name,
                        "type": item.type.name,
                        "stat": {
                            "mode": item.stat.mode,
                            "size": item.stat.size,
                            "created": item.stat.created.isoformat(),
                            "modified": item.stat.modified.isoformat(),
                        },
                        "symlink_target": item.symlink_target,
                    }
                    async for item in volume.scandir(
                        params["vfid"],
                        params["relpath"],
                    )
                ]
        return web.json_response(
            {
                "items": items,
            },
        )


async def rename_file(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("relpath"): tx.PurePath(relative_only=True),
                t.Key("new_name"): t.String(),
                t.Key("is_dir", default=False): t.ToBool,  # ignored since 22.03
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "rename_file", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            with handle_fs_errors(volume, params["vfid"]):
                await volume.move_file(
                    params["vfid"],
                    params["relpath"],
                    params["relpath"].with_name(params["new_name"]),
                )
        return web.Response(status=204)


async def move_file(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("src_relpath"): tx.PurePath(relative_only=True),
                t.Key("dst_relpath"): tx.PurePath(relative_only=True),
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "move_file", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            with handle_fs_errors(volume, params["vfid"]):
                await volume.move_file(
                    params["vfid"],
                    params["src_relpath"],
                    params["dst_relpath"],
                )
        return web.Response(status=204)


async def create_download_session(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("relpath"): tx.PurePath(relative_only=True),
                t.Key("archive", default=False): t.ToBool,
                t.Key("unmanaged_path", default=None): t.Null | t.String,
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "create_download_session", params)
        ctx: Context = request.app["ctx"]
        token_data = {
            "op": "download",
            "volume": params["volume"],
            "vfid": str(params["vfid"]),
            "relpath": str(params["relpath"]),
            "exp": datetime.utcnow() + ctx.local_config["storage-proxy"]["session-expire"],
        }
        token = jwt.encode(
            token_data,
            ctx.local_config["storage-proxy"]["secret"],
            algorithm="HS256",
        )
        return web.json_response(
            {
                "token": token,
            },
        )


async def create_upload_session(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("relpath"): tx.PurePath(relative_only=True),
                t.Key("size"): t.ToInt,
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "create_upload_session", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            session_id = await volume.prepare_upload(params["vfid"])
        token_data = {
            "op": "upload",
            "volume": params["volume"],
            "vfid": str(params["vfid"]),
            "relpath": str(params["relpath"]),
            "size": params["size"],
            "session": session_id,
            "exp": datetime.utcnow() + ctx.local_config["storage-proxy"]["session-expire"],
        }
        token = jwt.encode(
            token_data,
            ctx.local_config["storage-proxy"]["secret"],
            algorithm="HS256",
        )
        return web.json_response(
            {
                "token": token,
            },
        )


async def delete_files(request: web.Request) -> web.Response:
    async with check_params(
        request,
        t.Dict(
            {
                t.Key("volume"): t.String(),
                t.Key("vfid"): tx.UUID(),
                t.Key("relpaths"): t.List(tx.PurePath(relative_only=True)),
                t.Key("recursive", default=False): t.ToBool,
            },
        ),
    ) as params:
        await log_manager_api_entry(log, "delete_files", params)
        ctx: Context = request.app["ctx"]
        async with ctx.get_volume(params["volume"]) as volume:
            with handle_fs_errors(volume, params["vfid"]):
                await volume.delete_files(
                    params["vfid"],
                    params["relpaths"],
                    params["recursive"],
                )
        return web.json_response(
            {
                "status": "ok",
            },
        )


async def init_manager_app(ctx: Context) -> web.Application:
    app = web.Application(
        middlewares=[
            token_auth_middleware,
        ],
    )
    app["ctx"] = ctx
    app.router.add_route("GET", "/", get_status)
    app.router.add_route("GET", "/volumes", get_volumes)
    app.router.add_route("GET", "/volume/hwinfo", get_hwinfo)
    app.router.add_route("POST", "/folder/create", create_vfolder)
    app.router.add_route("POST", "/folder/delete", delete_vfolder)
    app.router.add_route("POST", "/folder/clone", clone_vfolder)
    app.router.add_route("GET", "/folder/mount", get_vfolder_mount)
    app.router.add_route("GET", "/volume/performance-metric", get_performance_metric)
    app.router.add_route("GET", "/folder/metadata", get_metadata)
    app.router.add_route("POST", "/folder/metadata", set_metadata)
    app.router.add_route("GET", "/volume/quota", get_quota)
    app.router.add_route("PATCH", "/volume/quota", set_quota)
    app.router.add_route("GET", "/folder/usage", get_vfolder_usage)
    app.router.add_route("GET", "/folder/fs-usage", get_vfolder_fs_usage)
    app.router.add_route("POST", "/folder/file/mkdir", mkdir)
    app.router.add_route("POST", "/folder/file/list", list_files)
    app.router.add_route("POST", "/folder/file/rename", rename_file)
    app.router.add_route("POST", "/folder/file/move", move_file)
    app.router.add_route("POST", "/folder/file/fetch", fetch_file)
    app.router.add_route("POST", "/folder/file/download", create_download_session)
    app.router.add_route("POST", "/folder/file/upload", create_upload_session)
    app.router.add_route("POST", "/folder/file/delete", delete_files)
    return app
