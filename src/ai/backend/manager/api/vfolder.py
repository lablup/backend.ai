from __future__ import annotations

import functools
import logging
import uuid
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Mapping,
    ParamSpec,
    Sequence,
    TypeAlias,
)

import aiotools
import attrs
import sqlalchemy as sa
from aiohttp import web
from pydantic import (
    Field,
)

from ai.backend.common.logging import BraceStyleAdapter

from ..models import (
    VFolderPermission,
    VFolderPermissionSetAlias,
    VFolderStatusSet,
    query_accessible_vfolders,
    vfolder_permissions,
    vfolder_status_map,
    vfolders,
)
from .exceptions import (
    InvalidAPIParameters,
    VFolderFilterStatusFailed,
    VFolderFilterStatusNotAvailable,
    VFolderNotFound,
)
from .utils import (
    BaseResponseModel,
)

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

VFolderRow: TypeAlias = Mapping[str, Any]
P = ParamSpec("P")


class SuccessResponseModel(BaseResponseModel):
    success: bool = Field(default=True)


async def check_vfolder_status(
    folder_row: VFolderRow,
    status: VFolderStatusSet,
) -> None:
    """
    Checks if the target vfolder status matches one of the status sets aliased by `status` VFolderStatusSet,
    and when check fails, raises VFolderFilterStatusFailed.
    This function should prevent user from accessing VFolders which are performing critical operations
    (e.g. VFolder cloning, removal, ...).
    This helper can be combined with `resolve_vfolders
    """

    available_vf_statuses = vfolder_status_map.get(status)
    if not available_vf_statuses:
        raise VFolderFilterStatusNotAvailable
    if folder_row["status"] not in available_vf_statuses:
        raise VFolderFilterStatusFailed


def with_vfolder_status_checked(
    status: VFolderStatusSet,
) -> Callable[
    [Callable[Concatenate[web.Request, VFolderRow, P], Awaitable[web.Response]]],
    Callable[Concatenate[web.Request, Sequence[VFolderRow], P], Awaitable[web.Response]],
]:
    """
    Checks if the target vfolder status matches one of the status sets aliased by `status` VFolderStatusSet.
    This function should prevent user from accessing VFolders which are performing critical operations
    (e.g. VFolder being cloned, being removed, ...).
    This helper can be combined with `resolve_vfolders
    """

    def _wrapper(
        handler: Callable[Concatenate[web.Request, VFolderRow, P], Awaitable[web.Response]],
    ) -> Callable[Concatenate[web.Request, Sequence[VFolderRow], P], Awaitable[web.Response]]:
        @functools.wraps(handler)
        async def _wrapped(
            request: web.Request,
            folder_rows: Sequence[VFolderRow],
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> web.Response:
            for row in folder_rows:
                try:
                    await check_vfolder_status(row, status)
                    return await handler(request, row, *args, **kwargs)
                except VFolderFilterStatusFailed:
                    pass
            # none of our candidates matched the status filter, so we should instead raise error here
            raise VFolderFilterStatusFailed

        return _wrapped

    return _wrapper


async def resolve_vfolder_rows(
    request: web.Request,
    perm: VFolderPermissionSetAlias | VFolderPermission | str,
    folder_id_or_name: str | uuid.UUID,
) -> Sequence[VFolderRow]:
    """
    Checks if the target VFolder exists and is either:
    - owned by requester, or
    - original owner (of target VFolder) has granted certain level of access to the requester

    When requester passes VFolder name to `folder_id_or_name` parameter then there is a possibility for
    this helper to return multiple entries of VFolder rows which are considered deleted,
    since Backend.AI also is aware of both deleted and purged VFolders. Resolving VFolder row by ID
    will not fall in such cases as it is guaranted by DB side that every VFolder ID is unique across whole table.
    To avoid such behavior, either do not consider VFolder name as an index to resolve VFolder row or
    pass every returned elements of this helper to a separate check_vfolder_status() call, so that
    the handler can figure out which row is the actual row that is aware of.
    """

    root_ctx: RootContext = request.app["_root.context"]
    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]
    allowed_vfolder_types = await root_ctx.shared_config.get_vfolder_types()
    vf_user_cond = None
    vf_group_cond = None

    match perm:
        case VFolderPermissionSetAlias():
            invited_perm_cond = vfolder_permissions.c.permission.in_(list(perm.value))
            if not request["is_admin"]:
                vf_group_cond = vfolders.c.permission.in_(list(perm.value))
        case _:
            # Otherwise, just compare it as-is (for future compatibility).
            invited_perm_cond = vfolder_permissions.c.permission == perm
            if not request["is_admin"]:
                vf_group_cond = vfolders.c.permission == perm

    match folder_id_or_name:
        case str():
            extra_vf_conds = vfolders.c.name == folder_id_or_name
        case uuid.UUID():
            extra_vf_conds = vfolders.c.id == folder_id_or_name
        case _:
            raise RuntimeError(f"Unsupported VFolder index type {type(folder_id_or_name)}")

    async with root_ctx.db.begin_readonly() as conn:
        entries = await query_accessible_vfolders(
            conn,
            user_uuid,
            user_role=user_role,
            domain_name=domain_name,
            allowed_vfolder_types=allowed_vfolder_types,
            extra_vf_conds=extra_vf_conds,
            extra_invited_vf_conds=invited_perm_cond,
            extra_vf_user_conds=vf_user_cond,
            extra_vf_group_conds=vf_group_cond,
        )
        if len(entries) == 0:
            raise VFolderNotFound(extra_data=folder_id_or_name)
        return entries


def with_vfolder_rows_resolved(
    perm: VFolderPermissionSetAlias | VFolderPermission,
) -> Callable[
    [Callable[Concatenate[web.Request, Sequence[VFolderRow], P], Awaitable[web.Response]]],
    Callable[Concatenate[web.Request, P], Awaitable[web.Response]],
]:
    """
    Decorator to pass result of `resolve_vfolder_rows()` to request handler. Index of VFolder is
    extracted from `name` path parameter. When multiple VFolder entries share same name, this decorator
    will pass every rows matching with the name and it is up to `with_vfolder_status_checked` decorator
    to filter out only row with its status matching the intention of the handler.
    Check documentation of `resolve_vfolder_rows()` for more information.
    """

    def _wrapper(
        handler: Callable[
            Concatenate[web.Request, Sequence[VFolderRow], P], Awaitable[web.Response]
        ],
    ) -> Callable[Concatenate[web.Request, P], Awaitable[web.Response]]:
        @functools.wraps(handler)
        async def _wrapped(request: web.Request, *args: P.args, **kwargs: P.kwargs) -> web.Response:
            folder_name = request.match_info["name"]
            return await handler(
                request, await resolve_vfolder_rows(request, perm, folder_name), *args, **kwargs
            )

        return _wrapped

    return _wrapper


def vfolder_check_exists(
    handler: Callable[Concatenate[web.Request, VFolderRow, P], Awaitable[web.Response]],
) -> Callable[Concatenate[web.Request, P], Awaitable[web.Response]]:
    """
    Checks if the target vfolder exists and is owned by the current user.

    The decorated handler should accept an extra "row" argument
    which contains the matched VirtualFolder table row.
    """

    @functools.wraps(handler)
    async def _wrapped(request: web.Request, *args: P.args, **kwargs: P.kwargs) -> web.Response:
        root_ctx: RootContext = request.app["_root.context"]
        user_uuid = request["user"]["uuid"]
        folder_name = request.match_info["name"]
        async with root_ctx.db.begin() as conn:
            j = sa.join(
                vfolders,
                vfolder_permissions,
                vfolders.c.id == vfolder_permissions.c.vfolder,
                isouter=True,
            )
            query = (
                sa.select("*")
                .select_from(j)
                .where(
                    ((vfolders.c.user == user_uuid) | (vfolder_permissions.c.user == user_uuid))
                    & (vfolders.c.name == folder_name)
                )
            )
            try:
                result = await conn.execute(query)
            except sa.exc.DataError:
                raise InvalidAPIParameters
            row = result.first()
            if row is None:
                raise VFolderNotFound()
        return await handler(request, row, *args, **kwargs)

    return _wrapped


async def storage_task_exception_handler(
    exc_type: type[Exception],
    exc_obj: Exception,
    tb: TracebackType,
):
    log.exception("Error while removing vFolder", exc_info=exc_obj)


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup
    storage_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["folders.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.storage_ptask_group = aiotools.PersistentTaskGroup(
        exception_handler=storage_task_exception_handler
    )


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["folders.context"]
    await app_ctx.database_ptask_group.shutdown()
    await app_ctx.storage_ptask_group.shutdown()


def create_app(default_cors_options):
    app = web.Application()
    app["prefix"] = "vfolder"
    app["api_versions"] = (2, 3, 4)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["folders.context"] = PrivateContext()
    return app, []
