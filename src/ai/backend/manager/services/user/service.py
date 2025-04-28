import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Awaitable, Callable, Mapping, Optional, cast
from uuid import UUID, uuid4

import aiotools
import msgpack
import sqlalchemy as sa
from dateutil.tz import tzutc
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline
from sqlalchemy.engine import Result, Row
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, noload
from sqlalchemy.sql.expression import bindparam

from ai.backend.common import redis_helper
from ai.backend.common.types import RedisConnectionInfo, VFolderID
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT, DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.errors.exceptions import VFolderOperationFailed
from ai.backend.manager.models import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    VFolderDeletionInfo,
    VFolderRow,
    VFolderStatusSet,
    initiate_vfolder_deletion,
    kernels,
    keypairs,
    vfolder_invitations,
    vfolder_permissions,
    vfolder_status_map,
    vfolders,
)
from ai.backend.manager.models.endpoint import (
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.error_logs import error_logs
from ai.backend.manager.models.gql_models.keypair import CreateKeyPair
from ai.backend.manager.models.group import ProjectType, association_groups_users, groups
from ai.backend.manager.models.kernel import RESOURCE_USAGE_KERNEL_STATUSES
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.session import (
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
    SessionRow,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus, users
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    SAConnection,
    execute_with_retry,
    execute_with_txn_retry,
)
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.user.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
)
from ai.backend.manager.services.user.actions.purge_user import (
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.user.type import UserData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


class UserService:
    _db: ExtendedAsyncSAEngine
    _storage_manager: StorageSessionManager
    _redis_stat: RedisConnectionInfo

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
        redis_stat: RedisConnectionInfo,
    ) -> None:
        self._db = db
        self._storage_manager = storage_manager
        self._redis_stat = redis_stat

    async def create_user(self, action: CreateUserAction) -> CreateUserActionResult:
        username = action.input.username if action.input.username else action.input.email
        _status = UserStatus.ACTIVE  # TODO: Need to be set in action explicitly not in service (integrate is_active and status)
        if action.input.status is None and action.input.is_active is not None:
            _status = UserStatus.ACTIVE if action.input.is_active else UserStatus.INACTIVE
        if action.input.status is not None:
            _status = action.input.status
        group_ids = [] if action.input.group_ids is None else action.input.group_ids

        user_data = {
            "username": username,
            "email": action.input.email,
            "password": action.input.password,
            "need_password_change": action.input.need_password_change,
            "full_name": action.input.full_name,
            "description": action.input.description,
            "status": _status,
            "status_info": "admin-requested",  # user mutation is only for admin
            "domain_name": action.input.domain_name,
            "role": action.input.role,
            "allowed_client_ip": action.input.allowed_client_ip,
            "totp_activated": action.input.totp_activated,
            "resource_policy": action.input.resource_policy,
            "sudo_session_enabled": action.input.sudo_session_enabled,
        }
        if action.input.container_uid is not None:
            user_data["container_uid"] = action.input.container_uid
        if action.input.container_main_gid is not None:
            user_data["container_main_gid"] = action.input.container_main_gid
        if action.input.container_gids is not None:
            user_data["container_gids"] = action.input.container_gids

        user_insert_query = sa.insert(users).values(user_data)

        async def _post_func(conn: SAConnection, result: Result) -> Optional[Row]:
            if result.rowcount == 0:
                return None
            created_user = result.first()

            # Create a default keypair for the user.
            email = action.input.email
            kp_data = CreateKeyPair.prepare_new_keypair(
                email,
                {
                    "is_active": _status == UserStatus.ACTIVE,
                    "is_admin": user_data["role"] in [UserRole.SUPERADMIN, UserRole.ADMIN],
                    "resource_policy": DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME,
                    "rate_limit": DEFAULT_KEYPAIR_RATE_LIMIT,
                },
            )
            kp_insert_query = sa.insert(keypairs).values(
                **kp_data,
                user=created_user.uuid,
            )
            await conn.execute(kp_insert_query)

            # Update user main_keypair
            main_ak = kp_data["access_key"]
            update_query = (
                sa.update(users)
                .where(users.c.uuid == created_user.uuid)
                .values(main_access_key=main_ak)
            )
            await conn.execute(update_query)

            model_store_query = sa.select([groups.c.id]).where(
                groups.c.type == ProjectType.MODEL_STORE
            )
            model_store_project = cast(
                dict[str, Any] | None, (await conn.execute(model_store_query)).first()
            )
            if model_store_project is not None:
                gids_to_join = [*group_ids, model_store_project["id"]]
            else:
                gids_to_join = group_ids

            # Add user to groups if group_ids parameter is provided.
            if gids_to_join:
                query = (
                    sa.select([groups.c.id])
                    .select_from(groups)
                    .where(groups.c.domain_name == action.input.domain_name)
                    .where(groups.c.id.in_(gids_to_join))
                )
                grps = (await conn.execute(query)).all()
                if grps:
                    group_data = [
                        {"user_id": created_user.uuid, "group_id": grp.id} for grp in grps
                    ]
                    group_insert_query = sa.insert(association_groups_users).values(group_data)
                    await conn.execute(group_insert_query)

            return created_user

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                query = user_insert_query.returning(user_insert_query.table)
                result = await conn.execute(query)
                created_user = await _post_func(conn, result)
                return MutationResult(
                    success=True if created_user is not None else False,
                    message="User created successfully",
                    data=created_user,
                )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)
        return CreateUserActionResult(
            data=UserData.from_row(result.data),
            success=result.success,
        )

    async def modify_user(self, action: ModifyUserAction) -> ModifyUserActionResult:
        email = action.email
        data = action.modifier.fields_to_update()
        if data.get("password") is None:
            data.pop("password", None)

        group_ids = action.group_ids.optional_value()

        if not data and group_ids is None:
            return ModifyUserActionResult(data=None, success=False)
        if data.get("status") is None and data.get("is_active") is not None:
            data["status"] = UserStatus.ACTIVE if data["is_active"] else UserStatus.INACTIVE

        if data.get("password") is not None:
            data["password_changed_at"] = sa.func.now()

        main_access_key: str | None = data.get("main_access_key")
        user_update_data: dict[str, Any] = {}
        prev_domain_name: str
        prev_role: UserRole

        async def _pre_func(conn: SAConnection) -> None:
            nonlocal user_update_data, prev_domain_name, prev_role, main_access_key
            result = await conn.execute(
                sa.select([users.c.domain_name, users.c.role, users.c.status])
                .select_from(users)
                .where(users.c.email == email),
            )
            row = result.first()
            prev_domain_name = row.domain_name
            prev_role = row.role
            user_update_data = data.copy()
            if "status" in data and row.status != data["status"]:
                user_update_data["status_info"] = (
                    "admin-requested"  # user mutation is only for admin
                )
            if main_access_key is not None:
                db_session = SASession(conn)
                keypair_query = (
                    sa.select(KeyPairRow)
                    .where(KeyPairRow.access_key == main_access_key)
                    .options(
                        noload("*"),
                        joinedload(KeyPairRow.user_row).options(load_only(UserRow.email)),
                    )
                )
                keypair_row: KeyPairRow | None = (await db_session.scalars(keypair_query)).first()
                if keypair_row is None:
                    raise RuntimeError("Cannot set non-existing access key as the main access key.")
                if keypair_row.user_row.email != email:
                    raise RuntimeError(
                        "Cannot set another user's access key as the main access key."
                    )
                await conn.execute(
                    sa.update(users)
                    .where(users.c.email == email)
                    .values(main_access_key=main_access_key)
                )

        update_query = lambda: (  # uses lambda because user_update_data is modified in _pre_func()
            sa.update(users).values(user_update_data).where(users.c.email == email)
        )

        async def _post_func(conn: SAConnection, result: Result) -> Row:
            nonlocal prev_domain_name, prev_role
            updated_user = result.first()
            if "role" in data and data["role"] != prev_role:
                from ai.backend.manager.models import keypairs

                result = await conn.execute(
                    sa.select([
                        keypairs.c.user,
                        keypairs.c.is_active,
                        keypairs.c.is_admin,
                        keypairs.c.access_key,
                    ])
                    .select_from(keypairs)
                    .where(keypairs.c.user == updated_user.uuid)
                    .order_by(sa.desc(keypairs.c.is_admin))
                    .order_by(sa.desc(keypairs.c.is_active)),
                )
                if data["role"] in [UserRole.SUPERADMIN, UserRole.ADMIN]:
                    # User's becomes admin. Set the keypair as active admin.
                    # TODO: Should we update the role of all users related to keypair?
                    kp = result.first()
                    kp_data = dict()
                    if not kp.is_admin:
                        kp_data["is_admin"] = True
                    if not kp.is_active:
                        kp_data["is_active"] = True
                    if kp_data:
                        await conn.execute(
                            sa.update(keypairs)
                            .values(kp_data)
                            .where(keypairs.c.user == updated_user.uuid),
                        )
                else:
                    # User becomes non-admin. Make the keypair non-admin as well.
                    # If there are multiple admin keypairs, inactivate them.
                    # TODO: Should elaborate keypair inactivation policy.
                    rows = result.fetchall()
                    kp_updates = []
                    for idx, row in enumerate(rows):
                        kp_data = {
                            "b_access_key": row.access_key,
                            "is_admin": row.is_admin,
                            "is_active": row.is_active,
                        }
                        if idx == 0:
                            kp_data["is_admin"] = False
                            kp_updates.append(kp_data)
                            continue
                        if row.is_admin and row.is_active:
                            kp_data["is_active"] = False
                            kp_updates.append(kp_data)
                    if kp_updates:
                        await conn.execute(
                            sa.update(keypairs)
                            .values({
                                "is_admin": bindparam("is_admin"),
                                "is_active": bindparam("is_active"),
                            })
                            .where(keypairs.c.access_key == bindparam("b_access_key")),
                            kp_updates,
                        )

            # If domain is changed and no group is associated, clear previous domain's group.
            if prev_domain_name != updated_user.domain_name and not group_ids:
                await conn.execute(
                    sa.delete(association_groups_users).where(
                        association_groups_users.c.user_id == updated_user.uuid
                    ),
                )

            # Update user's group if group_ids parameter is provided.
            if group_ids and updated_user is not None:
                # Clear previous groups associated with the user.
                await conn.execute(
                    sa.delete(association_groups_users).where(
                        association_groups_users.c.user_id == updated_user.uuid
                    ),
                )
                # Add user to new groups.
                result = await conn.execute(
                    sa.select([groups.c.id])
                    .select_from(groups)
                    .where(groups.c.domain_name == updated_user.domain_name)
                    .where(groups.c.id.in_(group_ids)),
                )
                grps = result.fetchall()
                if grps:
                    values = [{"user_id": updated_user.uuid, "group_id": grp.id} for grp in grps]
                    await conn.execute(
                        sa.insert(association_groups_users).values(values),
                    )

            return updated_user

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                await _pre_func(conn)
                query = update_query().returning(update_query().table)
                result = await conn.execute(query)
                updated_user = await _post_func(conn, result)

            return MutationResult(
                success=True,
                message="User modified successfully",
                data=updated_user,
            )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return ModifyUserActionResult(
            success=result.success,
            data=UserData.from_row(result.data),
        )

    async def delete_user(self, action: DeleteUserAction) -> DeleteUserActionResult:
        async def _pre_func(conn: SAConnection) -> None:
            # Make all user keypairs inactive.
            await conn.execute(
                sa.update(keypairs)
                .values(is_active=False)
                .where(keypairs.c.user_id == action.email),
            )

        update_query = (
            sa.update(users)
            .values(status=UserStatus.DELETED, status_info="admin-requested")
            .where(users.c.email == action.email)
        )

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                await _pre_func(conn)
                await conn.execute(update_query)

            return MutationResult(
                success=True,
                message="User deleted successfully",
                data=None,
            )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)
        return DeleteUserActionResult(
            success=result.success,
        )

    async def purge_user(self, action: PurgeUserAction) -> PurgeUserActionResult:
        email = action.email

        async def _delete(db_session: SASession) -> None:
            conn = await db_session.connection()
            user_uuid = await db_session.scalar(
                sa.select(UserRow.uuid).where(UserRow.email == email),
            )
            user_uuid = cast(Optional[UUID], user_uuid)
            log.info("Purging all records of the user {0}...", email)
            if user_uuid is None:
                raise RuntimeError(f"User not found (email: {email})")

            if await self.user_vfolder_mounted_to_active_kernels(conn, user_uuid):
                raise RuntimeError(
                    "Some of user's virtual folders are mounted to active kernels. "
                    "Terminate those kernels first.",
                )

            if action.purge_shared_vfolders.optional_value():
                await self.migrate_shared_vfolders(
                    conn,
                    deleted_user_uuid=user_uuid,
                    target_user_uuid=action.user_info_ctx.uuid,
                    target_user_email=action.user_info_ctx.email,
                )
            if action.delegate_endpoint_ownership.optional_value():
                await EndpointRow.delegate_endpoint_ownership(
                    db_session,
                    user_uuid,
                    action.user_info_ctx.uuid,
                    action.user_info_ctx.main_access_key,
                )
                await self._delete_endpoint(db_session, user_uuid, delete_destroyed_only=True)
            else:
                await self._delete_endpoint(db_session, user_uuid, delete_destroyed_only=False)
            if await self._user_has_active_sessions(db_session, user_uuid):
                raise RuntimeError("User has some active sessions. Terminate them first.")
            await self._delete_sessions(db_session, user_uuid)
            await self._delete_vfolders(self._db, user_uuid, self._storage_manager)
            await self.delete_error_logs(conn, user_uuid)
            await self.delete_keypairs(conn, self._redis_stat, user_uuid)

            await db_session.execute(sa.delete(users).where(users.c.email == email))

        async with self._db.connect() as db_conn:
            await execute_with_txn_retry(_delete, self._db.begin_session, db_conn)

        return PurgeUserActionResult(success=True)

    async def migrate_shared_vfolders(
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

        :param conn: DB connection
        :param deleted_user_uuid: user's UUID who will be deleted
        :param target_user_uuid: user's UUID who will get the ownership of virtual folders

        :return: number of deleted rows
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
            if rowcount > 0:
                log.info(
                    "{0} shared folders are detected and migrated to user {1}",
                    rowcount,
                    target_user_uuid,
                )
            return rowcount
        else:
            return 0

    async def _delete_vfolders(
        self,
        engine: ExtendedAsyncSAEngine,
        user_uuid: UUID,
        storage_manager: StorageSessionManager,
        *,
        delete_service: bool = False,
    ) -> int:
        """
        Delete user's all virtual folders as well as their physical data.

        :param conn: DB connection
        :param user_uuid: user's UUID to delete virtual folders

        :return: number of deleted rows
        """
        target_vfs: list[VFolderDeletionInfo] = []
        async with engine.begin_session() as db_session:
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
                target_vfs.append(
                    VFolderDeletionInfo(VFolderID.from_row(vf), vf.host, vf.unmanaged_path)
                )

        storage_ptask_group = aiotools.PersistentTaskGroup()
        try:
            await initiate_vfolder_deletion(
                engine,
                target_vfs,
                storage_manager,
                storage_ptask_group,
            )
        except VFolderOperationFailed as e:
            log.error("error on deleting vfolder filesystem directory: {0}", e.extra_msg)
            raise
        deleted_count = len(target_vfs)
        if deleted_count > 0:
            log.info("deleted {0} user's virtual folders ({1})", deleted_count, user_uuid)
        return deleted_count

    async def user_vfolder_mounted_to_active_kernels(
        self,
        conn: SAConnection,
        user_uuid: UUID,
    ) -> bool:
        """
        Check if no active kernel is using the user's virtual folders.

        :param conn: DB connection
        :param user_uuid: user's UUID

        :return: True if a virtual folder is mounted to active kernels.
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

    async def _user_has_active_sessions(
        self,
        db_session: SASession,
        user_uuid: UUID,
    ) -> bool:
        """
        Check if the user does not have active sessions.
        """
        active_session_count = await db_session.scalar(
            sa.select(sa.func.count())
            .select_from(SessionRow)
            .where(
                sa.and_(
                    SessionRow.user_uuid == user_uuid,
                    SessionRow.status.in_(AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES),
                )
            ),
        )
        return active_session_count > 0

    async def _delete_endpoint(
        self,
        db_session: SASession,
        user_uuid: UUID,
        *,
        delete_destroyed_only: bool = False,
    ) -> None:
        """
        Delete user's all endpoint.
        """
        if delete_destroyed_only:
            status_filter = {EndpointLifecycle.DESTROYED}
        else:
            status_filter = {status for status in EndpointLifecycle}
        endpoint_rows = await EndpointRow.list(
            db_session, user_uuid=user_uuid, load_tokens=True, status_filter=status_filter
        )
        token_ids_to_delete = []
        endpoint_ids_to_delete = []
        for row in endpoint_rows:
            token_ids_to_delete.extend([token.id for token in row.tokens])
            endpoint_ids_to_delete.append(row.id)
        await db_session.execute(
            sa.delete(EndpointTokenRow).where(EndpointTokenRow.id.in_(token_ids_to_delete))
        )
        await db_session.execute(
            sa.delete(EndpointRow).where(EndpointRow.id.in_(endpoint_ids_to_delete))
        )

    async def delete_error_logs(
        self,
        conn: SAConnection,
        user_uuid: UUID,
    ) -> int:
        """
        Delete user's all error logs.

        :param conn: DB connection
        :param user_uuid: user's UUID to delete error logs
        :return: number of deleted rows
        """
        result = await conn.execute(sa.delete(error_logs).where(error_logs.c.user == user_uuid))
        if result.rowcount > 0:
            log.info("deleted {0} user's error logs ({1})", result.rowcount, user_uuid)
        return result.rowcount

    async def _delete_sessions(
        self,
        db_session: SASession,
        user_uuid: UUID,
    ) -> None:
        """
        Delete user's sessions.
        """
        from ai.backend.manager.models.session import SessionRow

        await SessionRow.delete_by_user_id(user_uuid, db_session=db_session)

    async def delete_keypairs(
        self,
        conn: SAConnection,
        redis_conn: RedisConnectionInfo,
        user_uuid: UUID,
    ) -> int:
        """
        Delete user's all keypairs.

        :param conn: DB connection
        :param redis_conn: redis connection info
        :param user_uuid: user's UUID to delete keypairs
        :return: number of deleted rows
        """
        ak_rows = await conn.execute(
            sa.select([keypairs.c.access_key]).where(keypairs.c.user == user_uuid),
        )
        if (row := ak_rows.first()) and (access_key := row.access_key):
            # Log concurrency used only when there is at least one keypair.
            await redis_helper.execute(
                redis_conn,
                lambda r: r.delete(f"keypair.concurrency_used.{access_key}"),
            )
            await redis_helper.execute(
                redis_conn,
                lambda r: r.delete(f"keypair.sftp_concurrency_used.{access_key}"),
            )
        result = await conn.execute(
            sa.delete(keypairs).where(keypairs.c.user == user_uuid),
        )
        if result.rowcount > 0:
            log.info("deleted {0} user's keypairs ({1})", result.rowcount, user_uuid)
        return result.rowcount

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

    async def _get_time_binned_monthly_stats(self, user_uuid=None):
        """
        Generate time-binned (15 min) stats for the last one month (2880 points).
        The structure of the result would be:

            [
            # [
            #     timestamp, num_sessions,
            #     cpu_allocated, mem_allocated, gpu_allocated,
            #     io_read, io_write, scratch_used,
            # ]
                [1562083808.657106, 1, 1.2, 1073741824, ...],
                [1562084708.657106, 2, 4.0, 1073741824, ...],
            ]

        Note that the timestamp is in UNIX-timestamp.
        """
        # Get all or user kernels for the last month from DB.
        time_window = 900  # 15 min
        stat_length = 2880  # 15 * 4 * 24 * 30
        now = datetime.now(tzutc())
        start_date = now - timedelta(days=30)

        async with self._db.begin_readonly() as conn:
            query = (
                sa.select([
                    kernels.c.id,
                    kernels.c.created_at,
                    kernels.c.terminated_at,
                    kernels.c.occupied_slots,
                ])
                .select_from(kernels)
                .where(
                    (kernels.c.terminated_at >= start_date)
                    & (kernels.c.status.in_(RESOURCE_USAGE_KERNEL_STATUSES)),
                )
                .order_by(sa.asc(kernels.c.created_at))
            )
            if user_uuid is not None:
                query = query.where(kernels.c.user_uuid == user_uuid)
            result = await conn.execute(query)
            rows = result.fetchall()

        # Build time-series of time-binned stats.
        start_date_ts = start_date.timestamp()
        time_series_list: list[dict[str, Any]] = [
            {
                "date": start_date_ts + (idx * time_window),
                "num_sessions": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "cpu_allocated": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "mem_allocated": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "gpu_allocated": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "io_read_bytes": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "io_write_bytes": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "disk_used": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
            }
            for idx in range(stat_length)
        ]

        async def _pipe_builder(r: Redis) -> RedisPipeline:
            pipe = r.pipeline()
            for row in rows:
                await pipe.get(str(row["id"]))
            return pipe

        raw_stats = await redis_helper.execute(self._redis_stat, _pipe_builder)

        for row, raw_stat in zip(rows, raw_stats):
            if raw_stat is not None:
                last_stat = msgpack.unpackb(raw_stat)
                io_read_byte = int(nmget(last_stat, "io_read.current", 0))
                io_write_byte = int(nmget(last_stat, "io_write.current", 0))
                disk_used = int(nmget(last_stat, "io_scratch_size.stats.max", 0, "/"))
            else:
                io_read_byte = 0
                io_write_byte = 0
                disk_used = 0

            occupied_slots: Mapping[str, Any] = row.occupied_slots
            kernel_created_at: float = row.created_at.timestamp()
            kernel_terminated_at: float = row.terminated_at.timestamp()
            cpu_value = int(occupied_slots.get("cpu", 0))
            mem_value = int(occupied_slots.get("mem", 0))
            cuda_device_value = int(occupied_slots.get("cuda.devices", 0))
            cuda_share_value = Decimal(occupied_slots.get("cuda.shares", 0))

            start_index = int((kernel_created_at - start_date_ts) // time_window)
            end_index = int((kernel_terminated_at - start_date_ts) // time_window) + 1
            if start_index < 0:
                start_index = 0
            for time_series in time_series_list[start_index:end_index]:
                time_series["num_sessions"]["value"] += 1
                time_series["cpu_allocated"]["value"] += cpu_value
                time_series["mem_allocated"]["value"] += mem_value
                time_series["gpu_allocated"]["value"] += cuda_device_value
                time_series["gpu_allocated"]["value"] += cuda_share_value
                time_series["io_read_bytes"]["value"] += io_read_byte
                time_series["io_write_bytes"]["value"] += io_write_byte
                time_series["disk_used"]["value"] += disk_used

        # Change Decimal type to float to serialize to JSON
        for time_series in time_series_list:
            time_series["gpu_allocated"]["value"] = float(time_series["gpu_allocated"]["value"])
        return time_series_list

    async def user_month_stats(self, action: UserMonthStatsAction) -> UserMonthStatsActionResult:
        stats = await self._get_time_binned_monthly_stats(user_uuid=action.user_id)
        return UserMonthStatsActionResult(stats=stats)

    # TODO: user (전체)
    async def admin_month_stats(self, action: AdminMonthStatsAction) -> AdminMonthStatsActionResult:
        stats = await self._get_time_binned_monthly_stats(user_uuid=None)
        return AdminMonthStatsActionResult(stats=stats)
