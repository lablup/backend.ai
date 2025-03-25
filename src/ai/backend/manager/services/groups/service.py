import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, cast

import aiotools
import sqlalchemy as sa

from ai.backend.common.types import VFolderID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import VFolderOperationFailed
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SAConnection, execute_with_retry
from ai.backend.manager.services.groups.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.groups.actions.delete_group import (
    DeleteGroupAction,
    DeleteGroupActionResult,
)
from ai.backend.manager.services.groups.actions.modify_group import (
    ModifyGroupAction,
    ModifyGroupActionResult,
)
from ai.backend.manager.services.groups.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
)
from ai.backend.manager.services.groups.types import GroupData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


class GroupService:
    _db: ExtendedAsyncSAEngine
    _storage_manager: StorageSessionManager

    def __init__(self, db: ExtendedAsyncSAEngine, storage_manager: StorageSessionManager) -> None:
        self._db = db
        self._storage_manager = storage_manager

    async def create_group(self, action: CreateGroupAction) -> CreateGroupActionResult:
        data = action.get_insertion_data()
        base_query = sa.insert(groups).values(data)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                query = base_query.returning(base_query.table)
                result = await conn.execute(query)
                row = result.first()
                if result.rowcount > 0:
                    return MutationResult(
                        success=True, message=f"Group {action.name} creation succeed", data=row
                    )
                else:
                    return MutationResult(
                        success=False, message=f"no matching {action.name}", data=None
                    )

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return CreateGroupActionResult(data=GroupData.from_row(res.data), success=res.success)

    async def modify_group(self, action: ModifyGroupAction) -> ModifyGroupActionResult:
        data: dict[str, Any] = {}
        if action.name is not None:
            data["name"] = action.name
        if action.description is not None:
            data["description"] = action.description
        if action.is_active is not None:
            data["is_active"] = action.is_active
        if action.domain_name is not None:
            data["domain_name"] = action.domain_name
        if action.total_resource_slots is not None:
            data["total_resource_slots"] = action.total_resource_slots
        if action.allowed_vfolder_hosts is not None:
            data["allowed_vfolder_hosts"] = action.allowed_vfolder_hosts
        if action.integration_id is not None:
            data["integration_id"] = action.integration_id
        if action.resource_policy is not None:
            data["resource_policy"] = action.resource_policy
        if action.container_registry is not None:
            data["container_registry"] = action.container_registry

        if action.user_update_mode not in (None, "add", "remove"):
            raise ValueError("invalid user_update_mode")
        if not action.user_uuids:
            action.user_update_mode = None
        if not data and action.user_update_mode is None:
            return ModifyGroupActionResult(data=None, success=False)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                # TODO: refactor user addition/removal in groups as separate mutations
                #       (to apply since 21.09)
                gid = action.group_id
                if action.user_update_mode == "add":
                    assert action.user_uuids is not None
                    values = [{"user_id": uuid, "group_id": gid} for uuid in action.user_uuids]
                    await conn.execute(
                        sa.insert(association_groups_users).values(values),
                    )
                elif action.user_update_mode == "remove":
                    await conn.execute(
                        sa.delete(association_groups_users).where(
                            (association_groups_users.c.user_id.in_(action.user_uuids))
                            & (association_groups_users.c.group_id == gid),
                        ),
                    )
                if data:
                    result = await conn.execute(
                        sa.update(groups).values(data).where(groups.c.id == gid).returning(groups),
                    )
                    if result.rowcount > 0:
                        row = result.fist()
                        return MutationResult(success=True, message="success", data=row)
                    return MutationResult(success=False, message=f"no such group {gid}", data=None)
                else:  # updated association_groups_users table
                    return MutationResult(success=True, message="success", data=None)

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return ModifyGroupActionResult(data=GroupData.from_row(res.data), success=res.success)

    async def delete_group(self, action: DeleteGroupAction) -> DeleteGroupActionResult:
        update_query = (
            sa.update(groups)
            .values(
                is_active=False,
                integration_id=None,
            )
            .where(groups.c.id == action.group_id)
        )

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                result = await conn.execute(update_query)
                if result.rowcount > 0:
                    return MutationResult(success=True, message="success", data=None)
                return MutationResult(
                    success=False, message=f"no such group {action.group_id}", data=None
                )

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return DeleteGroupActionResult(data=GroupData.from_row(res.data), success=res.success)

    async def purge_group(self, action: PurgeGroupAction) -> PurgeGroupActionResult:
        gid = action.group_id

        async def _pre_func(conn: SAConnection) -> None:
            if await self.group_vfolder_mounted_to_active_kernels(conn, gid):
                raise RuntimeError(
                    "Some of virtual folders that belong to this group "
                    "are currently mounted to active sessions. "
                    "Terminate them first to proceed removal.",
                )
            if await self.group_has_active_kernels(conn, gid):
                raise RuntimeError(
                    "Group has some active session. Terminate them first to proceed removal.",
                )
            await self.delete_vfolders(gid)
            await self.delete_kernels(conn, gid)
            await self.delete_sessions(conn, gid)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                delete_query = sa.delete(groups).where(groups.c.id == gid)
                await _pre_func(conn)
                result = await conn.execute(delete_query)
                if result.rowcount > 0:
                    return MutationResult(
                        success=True, message=f"Group {action.group_id} deleted succeed", data=None
                    )
                else:
                    return MutationResult(
                        success=False, message=f"no matching {action.group_id}", data=None
                    )

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return PurgeGroupActionResult(data=GroupData.from_row(res.data), success=res.success)

    async def group_vfolder_mounted_to_active_kernels(
        self, db_conn: SAConnection, group_id: uuid.UUID
    ) -> bool:
        from ai.backend.manager.models import (
            AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
            kernels,
            vfolders,
        )

        query = sa.select([vfolders.c.id]).select_from(vfolders).where(vfolders.c.group == group_id)
        result = await db_conn.execute(query)
        rows = result.fetchall()
        group_vfolder_ids = [row["id"] for row in rows]
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            )
        )
        async for row in await db_conn.stream(query):
            for _mount in row["mounts"]:
                try:
                    vfolder_id = uuid.UUID(_mount[2])
                    if vfolder_id in group_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    async def group_has_active_kernels(self, db_conn: SAConnection, group_id: uuid.UUID) -> bool:
        from ai.backend.manager.models import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels

        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            )
        )
        active_kernel_count = await db_conn.scalar(query)
        return True if active_kernel_count > 0 else False

    async def delete_vfolders(self, group_id: uuid.UUID) -> int:
        from ai.backend.manager.models import (
            VFolderDeletionInfo,
            VFolderRow,
            VFolderStatusSet,
            initiate_vfolder_deletion,
            vfolder_status_map,
        )

        target_vfs: list[VFolderDeletionInfo] = []
        async with self._db.begin_session() as db_session:
            query = sa.select(VFolderRow).where(
                sa.and_(
                    VFolderRow.group == group_id,
                    VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.DELETABLE]),
                )
            )
            result = await db_session.scalars(query)
            rows = cast(list[VFolderRow], result.fetchall())
            for vf in rows:
                target_vfs.append(
                    VFolderDeletionInfo(VFolderID.from_row(vf), vf.host, vf.unmanaged_path)
                )

        storage_ptask_group = aiotools.PersistentTaskGroup()
        try:
            await initiate_vfolder_deletion(
                self._db,
                target_vfs,
                self._storage_manager,
                storage_ptask_group,
            )
        except VFolderOperationFailed as e:
            log.error("error on deleting vfolder filesystem directory: {0}", e.extra_msg)
            raise
        deleted_count = len(target_vfs)
        if deleted_count > 0:
            log.info("deleted {0} group's virtual folders ({1})", deleted_count, group_id)
        return deleted_count

    async def delete_kernels(self, db_conn: SAConnection, group_id: uuid.UUID) -> None:
        from ai.backend.manager.models import kernels

        query = sa.delete(kernels).where(kernels.c.group_id == group_id)
        result = await db_conn.execute(query)
        if result.rowcount > 0:
            log.info("deleted {0} group's kernels ({1})", result.rowcount, group_id)
        return result.rowcount

    async def delete_sessions(self, db_conn: SAConnection, group_id: uuid.UUID) -> None:
        from ai.backend.manager.models.session import SessionRow

        stmt = sa.delete(SessionRow).where(SessionRow.group_id == group_id)
        await db_conn.execute(stmt)

    async def _db_mutation_wrapper(
        self, _do_mutate: Callable[[], Awaitable[MutationResult]]
    ) -> MutationResult:
        try:
            return await execute_with_retry(_do_mutate)
        except sa.exc.IntegrityError as e:
            log.warning("db_mutation_wrapper(): integrity error ({})", repr(e))
            return MutationResult(success=False, message=f"integrity error: {e}", data=None)
        except sa.exc.StatementError as e:
            log.warning(
                "db_mutation_wrapper(): statement error ({})\n{}",
                repr(e),
                e.statement or "(unknown)",
            )
            orig_exc = e.orig
            return MutationResult(success=False, message=str(orig_exc), data=None)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception:
            log.exception("db_mutation_wrapper(): other error")
            raise
