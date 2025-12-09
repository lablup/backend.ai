import uuid

import aiotools
import sqlalchemy as sa

from ai.backend.common.types import VFolderID
from ai.backend.manager.errors.resource import (
    ProjectHasActiveEndpointsError,
    ProjectHasActiveKernelsError,
    ProjectHasVFoldersMountedError,
    ProjectNotFound,
)
from ai.backend.manager.errors.storage import VFolderOperationFailed
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SASession


class AdminGroupRepository:
    _db: ExtendedAsyncSAEngine
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._db = db
        self._storage_manager = storage_manager

    async def _check_group_vfolders_mounted_to_active_kernels(
        self, session: SASession, group_id: uuid.UUID
    ) -> bool:
        """Check if group has vfolders mounted to active kernels."""
        from ai.backend.manager.models import (
            AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
            kernels,
            vfolders,
        )

        # Get group vfolder IDs
        query = sa.select([vfolders.c.id]).select_from(vfolders).where(vfolders.c.group == group_id)
        result = await session.execute(query)
        rows = result.fetchall()
        group_vfolder_ids = [row["id"] for row in rows]

        # Check if any active kernels have these vfolders mounted
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            )
        )
        async for row in await session.stream(query):
            for _mount in row["mounts"]:
                try:
                    vfolder_id = uuid.UUID(_mount[2])
                    if vfolder_id in group_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    async def _check_group_has_active_kernels(
        self, session: SASession, group_id: uuid.UUID
    ) -> bool:
        """Check if group has active kernels."""
        from ai.backend.manager.models import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels

        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            )
        )
        active_kernel_count = await session.scalar(query)
        return True if active_kernel_count > 0 else False

    async def _delete_group_vfolders(self, group_id: uuid.UUID) -> int:
        """Delete all vfolders belonging to the group."""
        from typing import cast

        from ai.backend.manager.models import (
            VFolderDeletionInfo,
            VFolderRow,
            VFolderStatusSet,
            initiate_vfolder_deletion,
            vfolder_status_map,
        )

        target_vfs: list[VFolderDeletionInfo] = []
        async with self._db.begin_session() as session:
            query = sa.select(VFolderRow).where(
                sa.and_(
                    VFolderRow.group == group_id,
                    VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.DELETABLE]),
                )
            )
            result = await session.scalars(query)
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
        except VFolderOperationFailed:
            raise

        return len(target_vfs)

    async def _delete_group_kernels(self, session: SASession, group_id: uuid.UUID) -> int:
        """Delete all kernels belonging to the group."""
        from ai.backend.manager.models import kernels

        query = sa.delete(kernels).where(kernels.c.group_id == group_id)
        result = await session.execute(query)
        return result.rowcount

    async def _delete_group_sessions(self, session: SASession, group_id: uuid.UUID) -> int:
        """Delete all sessions belonging to the group."""
        stmt = sa.delete(SessionRow).where(SessionRow.group_id == group_id)
        result = await session.execute(stmt)
        return result.rowcount

    async def _delete_group_endpoints(self, session: SASession, group_id: uuid.UUID) -> None:
        """Delete all endpoints belonging to the group."""
        # Get all endpoints for the group
        endpoints = (
            await session.execute(
                sa.select(
                    EndpointRow.id,
                    sa.case(
                        (
                            EndpointRow.lifecycle_stage.in_([
                                EndpointLifecycle.CREATED,
                                EndpointLifecycle.DESTROYING,
                            ]),
                            True,
                        ),
                        else_=False,
                    ).label("is_active"),
                ).where(EndpointRow.project == group_id)
            )
        ).all()

        if len(endpoints) == 0:
            return

        # Check for active endpoints
        active_endpoints = [ep.id for ep in endpoints if ep.is_active]
        if len(active_endpoints) > 0:
            raise ProjectHasActiveEndpointsError(f"project {group_id} has active endpoints")

        # Delete endpoint-related data
        endpoint_ids = [ep.id for ep in endpoints]

        # Get session IDs before deleting endpoints
        session_ids_result = await session.scalars(
            sa.select(RoutingRow.session).where(
                sa.and_(
                    RoutingRow.endpoint.in_(endpoint_ids),
                    RoutingRow.session.is_not(None),
                )
            )
        )
        session_ids = list(session_ids_result.unique().all())

        # Delete endpoints (routings are CASCADE deleted automatically)
        await session.execute(
            sa.delete(EndpointRow).where(EndpointRow.id.in_(endpoint_ids)),
            execution_options={"synchronize_session": False},
        )

        # Delete sessions that were associated with endpoints
        if session_ids:
            await session.execute(
                sa.delete(SessionRow).where(SessionRow.id.in_(session_ids)),
                execution_options={"synchronize_session": False},
            )

    async def purge_group_force(self, group_id: uuid.UUID) -> bool:
        """Completely remove a group and all its associated data."""
        async with self._db.begin_session() as session:
            # Pre-flight checks
            if await self._check_group_vfolders_mounted_to_active_kernels(session, group_id):
                raise ProjectHasVFoldersMountedError(
                    f"error on deleting project {group_id} with vfolders mounted to active kernels"
                )

            if await self._check_group_has_active_kernels(session, group_id):
                raise ProjectHasActiveKernelsError(
                    f"error on deleting project {group_id} with active kernels"
                )

            # Delete associated resources
            await self._delete_group_endpoints(session, group_id)

            # Commit session before vfolder deletion (which uses separate transactions)
            await session.commit()

        # Delete vfolders (uses separate transaction)
        await self._delete_group_vfolders(group_id)

        async with self._db.begin_session() as session:
            # Delete remaining data
            await self._delete_group_kernels(session, group_id)
            await self._delete_group_sessions(session, group_id)

            # Finally delete the group itself
            result = await session.execute(sa.delete(groups).where(groups.c.id == group_id))

            if result.rowcount > 0:
                return True
            raise ProjectNotFound("project not found")
