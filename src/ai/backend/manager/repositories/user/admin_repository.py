from typing import Optional, cast
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import AccessKey
from ai.backend.manager.errors.auth import UserNotFound
from ai.backend.manager.errors.storage import VFolderOperationFailed
from ai.backend.manager.models import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    VFolderDeletionInfo,
    VFolderRow,
    VFolderStatusSet,
    initiate_vfolder_deletion,
    kernels,
    vfolder_invitations,
    vfolder_status_map,
)
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow, EndpointTokenRow
from ai.backend.manager.models.error_logs import error_logs
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.session import (
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
    QueryCondition,
    QueryOption,
    SessionRow,
    by_status,
    by_user_id,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.types import join_by_related_field
from ai.backend.manager.models.user import UserRow, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SAConnection
from ai.backend.manager.models.vfolder import vfolder_permissions, vfolders


class AdminUserRepository:
    """
    Repository for admin-specific user operations that bypass ownership checks.
    This should only be used by superadmin users.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def purge_user_force(self, email: str) -> None:
        """
        Completely purge user and all associated data.
        Admin-only operation with no ownership validation.
        """
        async with self._db.begin() as conn:
            user_uuid = await self._get_user_uuid_by_email(conn, email)
            if not user_uuid:
                raise UserNotFound()

            # Delete all user data in proper order
            await self._delete_error_logs(conn, user_uuid)
            await self._delete_keypairs(conn, user_uuid)
            await self._delete_vfolder_permissions(conn, user_uuid)
            await self._clear_user_groups(conn, user_uuid)

            # Finally delete the user
            await conn.execute(sa.delete(users).where(users.c.email == email))

    async def check_user_vfolder_mounted_to_active_kernels_force(self, user_uuid: UUID) -> bool:
        """
        Check if user's vfolders are mounted to active kernels.
        Admin-only operation that bypasses ownership validation.
        """
        async with self._db.begin() as conn:
            return await self._user_vfolder_mounted_to_active_kernels(conn, user_uuid)

    async def migrate_shared_vfolders_force(
        self,
        deleted_user_uuid: UUID,
        target_user_uuid: UUID,
        target_user_email: str,
    ) -> int:
        """
        Migrate shared virtual folders ownership to target user.
        Admin-only operation that bypasses ownership validation.
        """
        async with self._db.begin() as conn:
            return await self._migrate_shared_vfolders(
                conn, deleted_user_uuid, target_user_uuid, target_user_email
            )

    async def delete_user_vfolders_force(
        self,
        user_uuid: UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """
        Delete user's all virtual folders and their physical data.
        Admin-only operation.
        """
        return await self._delete_vfolders(user_uuid, storage_manager)

    async def retrieve_active_sessions_force(self, user_uuid: UUID) -> list[SessionRow]:
        """
        Retrieve active sessions for a user.
        Admin-only operation that bypasses ownership validation.
        """
        query_conditions: list[QueryCondition] = [
            by_user_id(user_uuid),
            by_status(AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES),
        ]

        query_options: list[QueryOption] = [
            join_by_related_field(SessionRow.user),
        ]

        return await SessionRow.list_session_by_condition(
            query_conditions, query_options, db=self._db
        )

    async def delete_user_keypairs_with_valkey_force(
        self,
        user_uuid: UUID,
        valkey_stat_client: ValkeyStatClient,
    ) -> int:
        """
        Delete user's keypairs including Valkey concurrency cleanup.
        Admin-only operation.
        """
        async with self._db.begin() as conn:
            return await self._delete_keypairs_with_valkey(conn, valkey_stat_client, user_uuid)

    async def delegate_endpoint_ownership_force(
        self,
        user_uuid: UUID,
        target_user_uuid: UUID,
        target_main_access_key: AccessKey,
    ) -> None:
        """
        Delegate endpoint ownership to another user.
        Admin-only operation.
        """
        async with self._db.begin_session() as session:
            await EndpointRow.delegate_endpoint_ownership(
                session, user_uuid, target_user_uuid, target_main_access_key
            )

    async def delete_endpoints_force(
        self,
        user_uuid: UUID,
        delete_destroyed_only: bool = False,
    ) -> None:
        """
        Delete user's endpoints.
        Admin-only operation.
        """
        async with self._db.begin_session() as session:
            await self._delete_endpoints(session, user_uuid, delete_destroyed_only)

    async def get_admin_time_binned_monthly_stats_force(
        self,
        valkey_stat_client: ValkeyStatClient,
    ) -> list[dict]:
        """
        Get time-binned monthly statistics for all users.
        Admin-only operation that bypasses ownership validation.
        """
        from ai.backend.manager.repositories.user.repository import UserRepository

        # Create a temporary UserRepository instance to reuse the statistics logic
        user_repo = UserRepository(self._db)
        return await user_repo._get_time_binned_monthly_stats(None, valkey_stat_client)

    async def _get_user_by_email(self, session: SASession, email: str) -> Optional[UserRow]:
        """Private method to get user by email."""
        return await session.scalar(sa.select(UserRow).where(UserRow.email == email))

    async def _get_user_by_uuid(self, session: SASession, user_uuid: UUID) -> Optional[UserRow]:
        """Private method to get user by UUID."""
        return await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_uuid))

    async def _get_user_uuid_by_email(self, conn: SAConnection, email: str) -> Optional[UUID]:
        """Private method to get user UUID by email."""
        result = await conn.execute(sa.select(users.c.uuid).where(users.c.email == email))
        row = result.first()
        return row.uuid if row else None

    async def _delete_error_logs(self, conn: SAConnection, user_uuid: UUID) -> int:
        """Private method to delete user's error logs."""
        result = await conn.execute(sa.delete(error_logs).where(error_logs.c.user == user_uuid))
        return result.rowcount

    async def _delete_keypairs(self, conn: SAConnection, user_uuid: UUID) -> int:
        """Private method to delete user's keypairs."""
        result = await conn.execute(sa.delete(keypairs).where(keypairs.c.user == user_uuid))
        return result.rowcount

    async def _delete_vfolder_permissions(self, conn: SAConnection, user_uuid: UUID) -> int:
        """Private method to delete user's vfolder permissions."""
        result = await conn.execute(
            sa.delete(vfolder_permissions).where(vfolder_permissions.c.user == user_uuid)
        )
        return result.rowcount

    async def _clear_user_groups(self, conn: SAConnection, user_uuid: UUID) -> None:
        """Private method to clear user's group associations."""
        await conn.execute(
            sa.delete(association_groups_users).where(
                association_groups_users.c.user_id == user_uuid
            )
        )

    async def _user_vfolder_mounted_to_active_kernels(
        self,
        conn: SAConnection,
        user_uuid: UUID,
    ) -> bool:
        """
        Check if no active kernel is using the user's virtual folders.
        """
        result = await conn.execute(
            sa.select([vfolders.c.id]).select_from(vfolders).where(vfolders.c.user == user_uuid),
        )
        rows = result.fetchall()
        user_vfolder_ids = [row.id for row in rows]
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        async for row in await conn.stream(query):
            for _mount in row["mounts"]:
                try:
                    vfolder_id = UUID(_mount[2])
                    if vfolder_id in user_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    async def _migrate_shared_vfolders(
        self,
        conn: SAConnection,
        deleted_user_uuid: UUID,
        target_user_uuid: UUID,
        target_user_email: str,
    ) -> int:
        """
        Migrate shared virtual folders' ownership to a target user.
        If migrating virtual folder's name collides with target user's already
        existing folder, append random string to the migrating one.
        """
        # Gather target user's virtual folders' names.
        query = (
            sa.select([vfolders.c.name])
            .select_from(vfolders)
            .where(vfolders.c.user == target_user_uuid)
        )
        existing_vfolder_names = [row.name async for row in (await conn.stream(query))]

        # Migrate shared virtual folders.
        # If virtual folder's name collides with target user's folder,
        # append random string to the name of the migrating folder.
        j = vfolder_permissions.join(
            vfolders,
            vfolder_permissions.c.vfolder == vfolders.c.id,
        )
        query = (
            sa.select([vfolders.c.id, vfolders.c.name])
            .select_from(j)
            .where(vfolders.c.user == deleted_user_uuid)
        )
        migrate_updates = []
        async for row in await conn.stream(query):
            name = row.name
            if name in existing_vfolder_names:
                name += f"-{uuid4().hex[:10]}"
            migrate_updates.append({"vid": row.id, "vname": name})

        if migrate_updates:
            # Remove invitations and vfolder_permissions from target user.
            # Target user will be the new owner, and it does not make sense to have
            # invitation and shared permission for its own folder.
            migrate_vfolder_ids = [item["vid"] for item in migrate_updates]
            delete_query = sa.delete(vfolder_invitations).where(
                (vfolder_invitations.c.invitee == target_user_email)
                & (vfolder_invitations.c.vfolder.in_(migrate_vfolder_ids))
            )
            await conn.execute(delete_query)
            delete_query = sa.delete(vfolder_permissions).where(
                (vfolder_permissions.c.user == target_user_uuid)
                & (vfolder_permissions.c.vfolder.in_(migrate_vfolder_ids))
            )
            await conn.execute(delete_query)

            rowcount = 0
            for item in migrate_updates:
                update_query = (
                    sa.update(vfolders)
                    .values(
                        user=target_user_uuid,
                        name=item["vname"],
                    )
                    .where(vfolders.c.id == item["vid"])
                )
                result = await conn.execute(update_query)
                rowcount += result.rowcount
            return rowcount
        else:
            return 0

    async def _delete_vfolders(
        self,
        user_uuid: UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """
        Delete user's all virtual folders as well as their physical data.
        """
        import aiotools

        target_vfs: list[VFolderDeletionInfo] = []
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                vfolder_permissions.delete().where(vfolder_permissions.c.user == user_uuid),
            )
            result = await db_session.scalars(
                sa.select(VFolderRow).where(
                    sa.and_(
                        VFolderRow.user == user_uuid,
                        VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.DELETABLE]),
                    )
                ),
            )
            rows = cast(list[VFolderRow], result.fetchall())
            for vf in rows:
                from ai.backend.common.types import VFolderID

                target_vfs.append(
                    VFolderDeletionInfo(VFolderID.from_row(vf), vf.host, vf.unmanaged_path)
                )

        storage_ptask_group = aiotools.PersistentTaskGroup()
        try:
            await initiate_vfolder_deletion(
                self._db,
                target_vfs,
                storage_manager,
                storage_ptask_group,
            )
        except VFolderOperationFailed:
            raise

        deleted_count = len(target_vfs)
        return deleted_count

    async def _delete_keypairs_with_valkey(
        self,
        conn: SAConnection,
        valkey_stat_client: ValkeyStatClient,
        user_uuid: UUID,
    ) -> int:
        """
        Delete user's all keypairs with Valkey cleanup.
        """
        ak_rows = await conn.execute(
            sa.select([keypairs.c.access_key]).where(keypairs.c.user == user_uuid),
        )
        if (row := ak_rows.first()) and (access_key := row.access_key):
            # Log concurrency used only when there is at least one keypair.
            await valkey_stat_client.delete_keypair_concurrency(
                access_key=access_key,
                is_private=False,
            )
            await valkey_stat_client.delete_keypair_concurrency(
                access_key=access_key,
                is_private=True,
            )
        result = await conn.execute(
            sa.delete(keypairs).where(keypairs.c.user == user_uuid),
        )
        return result.rowcount

    async def _delete_endpoints(
        self,
        session: SASession,
        user_uuid: UUID,
        delete_destroyed_only: bool = False,
    ) -> None:
        """Private method to delete user's endpoints."""
        if delete_destroyed_only:
            status_filter = {EndpointLifecycle.DESTROYED}
        else:
            status_filter = {status for status in EndpointLifecycle}

        endpoint_rows = await EndpointRow.list(
            session, user_uuid=user_uuid, load_tokens=True, status_filter=status_filter
        )

        token_ids_to_delete = []
        endpoint_ids_to_delete = []
        for row in endpoint_rows:
            token_ids_to_delete.extend([token.id for token in row.tokens])
            endpoint_ids_to_delete.append(row.id)

        if token_ids_to_delete:
            await session.execute(
                sa.delete(EndpointTokenRow).where(EndpointTokenRow.id.in_(token_ids_to_delete))
            )

        if endpoint_ids_to_delete:
            await session.execute(
                sa.delete(EndpointRow).where(EndpointRow.id.in_(endpoint_ids_to_delete))
            )
