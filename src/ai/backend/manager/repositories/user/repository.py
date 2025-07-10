import logging
from datetime import datetime, timedelta
from typing import Any, Optional, cast
from uuid import UUID, uuid4

import aiotools
import sqlalchemy as sa
from dateutil.tz import tzutc
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline
from sqlalchemy.engine import Result, Row
from sqlalchemy.orm import joinedload, load_only, noload
from sqlalchemy.sql.expression import bindparam

from ai.backend.common import redis_helper
from ai.backend.common.types import RedisConnectionInfo, VFolderID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.keypair.types import KeyPairCreator
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
from ai.backend.manager.models.group import ProjectType, association_groups_users, groups
from ai.backend.manager.models.kernel import RESOURCE_USAGE_KERNEL_STATUSES
from ai.backend.manager.models.keypair import KeyPairRow, prepare_new_keypair
from ai.backend.manager.models.session import (
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
    QueryCondition,
    QueryOption,
    RelatedFields,
    SessionRow,
    and_status,
    and_user_id,
    join_related_field,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus, users
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    SAConnection,
)
from ai.backend.manager.registry import AgentRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserRepository:
    _db: ExtendedAsyncSAEngine
    _storage_manager: StorageSessionManager
    _redis_stat: RedisConnectionInfo
    _agent_registry: AgentRegistry

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
        redis_stat: RedisConnectionInfo,
        agent_registry: AgentRegistry,
    ) -> None:
        self._db = db
        self._storage_manager = storage_manager
        self._redis_stat = redis_stat
        self._agent_registry = agent_registry

    async def create_user(self, user_data: dict[str, Any], group_ids: list[UUID]) -> Optional[Row]:
        user_insert_query = sa.insert(users).values(user_data)

        async def _post_func(conn: SAConnection, result: Result) -> Optional[Row]:
            if result.rowcount == 0:
                return None
            created_user = result.first()

            email = user_data["email"]
            status = user_data["status"]
            role = user_data["role"]
            domain_name = user_data["domain_name"]

            keypair_creator = KeyPairCreator(
                is_active=(status == UserStatus.ACTIVE),
                is_admin=role in [UserRole.SUPERADMIN, UserRole.ADMIN],
                resource_policy=DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME,
                rate_limit=DEFAULT_KEYPAIR_RATE_LIMIT,
            )
            kp_data = prepare_new_keypair(email, keypair_creator)
            kp_insert_query = sa.insert(keypairs).values(
                **kp_data,
                user=created_user.uuid,
            )
            await conn.execute(kp_insert_query)

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

            if gids_to_join:
                query = (
                    sa.select([groups.c.id])
                    .select_from(groups)
                    .where(groups.c.domain_name == domain_name)
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

        async with self._db.begin() as conn:
            query = user_insert_query.returning(user_insert_query.table)
            result = await conn.execute(query)
            created_user = await _post_func(conn, result)
            return created_user

    async def get_user_domain_and_role(self, email: str) -> tuple[str, UserRole, UserStatus]:
        async with self._db.begin_readonly() as conn:
            result = await conn.execute(
                sa.select([users.c.domain_name, users.c.role, users.c.status])
                .select_from(users)
                .where(users.c.email == email),
            )
            row = result.first()
            return row.domain_name, row.role, row.status

    async def validate_main_access_key(self, email: str, main_access_key: str) -> None:
        async with self._db.begin_session() as db_session:
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
                raise RuntimeError("Cannot set another user's access key as the main access key.")

    async def update_user_main_access_key(self, email: str, main_access_key: str) -> None:
        async with self._db.begin() as conn:
            await conn.execute(
                sa.update(users)
                .where(users.c.email == email)
                .values(main_access_key=main_access_key)
            )

    async def update_user(self, email: str, user_update_data: dict[str, Any]) -> Optional[Row]:
        update_query = sa.update(users).values(user_update_data).where(users.c.email == email)

        async with self._db.begin() as conn:
            query = update_query.returning(update_query.table)
            result = await conn.execute(query)
            return result.first()

    async def update_user_keypairs_role(self, user_uuid: UUID, new_role: UserRole) -> None:
        async with self._db.begin() as conn:
            result = await conn.execute(
                sa.select([
                    keypairs.c.user,
                    keypairs.c.is_active,
                    keypairs.c.is_admin,
                    keypairs.c.access_key,
                ])
                .select_from(keypairs)
                .where(keypairs.c.user == user_uuid)
                .order_by(sa.desc(keypairs.c.is_admin))
                .order_by(sa.desc(keypairs.c.is_active)),
            )

            if new_role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
                kp = result.first()
                kp_data = dict()
                if not kp.is_admin:
                    kp_data["is_admin"] = True
                if not kp.is_active:
                    kp_data["is_active"] = True
                if kp_data:
                    await conn.execute(
                        sa.update(keypairs).values(kp_data).where(keypairs.c.user == user_uuid),
                    )
            else:
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

    async def clear_user_groups(self, user_uuid: UUID) -> None:
        async with self._db.begin() as conn:
            await conn.execute(
                sa.delete(association_groups_users).where(
                    association_groups_users.c.user_id == user_uuid
                ),
            )

    async def update_user_groups(
        self, user_uuid: UUID, domain_name: str, group_ids: list[UUID]
    ) -> None:
        async with self._db.begin() as conn:
            await conn.execute(
                sa.delete(association_groups_users).where(
                    association_groups_users.c.user_id == user_uuid
                ),
            )

            result = await conn.execute(
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == domain_name)
                .where(groups.c.id.in_(group_ids)),
            )
            grps = result.fetchall()
            if grps:
                values = [{"user_id": user_uuid, "group_id": grp.id} for grp in grps]
                await conn.execute(
                    sa.insert(association_groups_users).values(values),
                )

    async def deactivate_user_keypairs(self, email: str) -> None:
        async with self._db.begin() as conn:
            await conn.execute(
                sa.update(keypairs).values(is_active=False).where(keypairs.c.user_id == email),
            )

    async def delete_user(self, email: str) -> None:
        async with self._db.begin() as conn:
            await conn.execute(
                sa.update(users)
                .values(status=UserStatus.DELETED, status_info="admin-requested")
                .where(users.c.email == email)
            )

    async def get_user_uuid_by_email(self, email: str) -> Optional[UUID]:
        async with self._db.begin_session() as db_session:
            user_uuid = await db_session.scalar(
                sa.select(UserRow.uuid).where(UserRow.email == email),
            )
            return cast(Optional[UUID], user_uuid)

    async def user_vfolder_mounted_to_active_kernels(self, user_uuid: UUID) -> bool:
        async with self._db.begin() as conn:
            result = await conn.execute(
                sa.select([vfolders.c.id])
                .select_from(vfolders)
                .where(vfolders.c.user == user_uuid),
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

    async def migrate_shared_vfolders(
        self,
        deleted_user_uuid: UUID,
        target_user_uuid: UUID,
        target_user_email: str,
    ) -> int:
        async with self._db.begin() as conn:
            query = (
                sa.select([vfolders.c.name])
                .select_from(vfolders)
                .where(vfolders.c.user == target_user_uuid)
            )
            existing_vfolder_names = [row.name async for row in (await conn.stream(query))]

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

    async def delete_vfolders(self, user_uuid: UUID) -> int:
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
            log.info("deleted {0} user's virtual folders ({1})", deleted_count, user_uuid)
        return deleted_count

    async def retrieve_active_sessions(self, user_uuid: UUID) -> list[SessionRow]:
        query_conditions: list[QueryCondition] = [
            and_user_id(user_uuid),
            and_status(AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES),
        ]

        query_options: list[QueryOption] = [
            join_related_field(RelatedFields.USER),
        ]

        session_rows = await SessionRow.list_session_by_condition(
            query_conditions, query_options, db=self._db
        )

        return session_rows

    async def delete_endpoint(
        self,
        user_uuid: UUID,
        delete_destroyed_only: bool = False,
    ) -> None:
        async with self._db.begin_session() as db_session:
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

    async def delete_error_logs(self, user_uuid: UUID) -> int:
        async with self._db.begin() as conn:
            result = await conn.execute(sa.delete(error_logs).where(error_logs.c.user == user_uuid))
            if result.rowcount > 0:
                log.info("deleted {0} user's error logs ({1})", result.rowcount, user_uuid)
            return result.rowcount

    async def delete_keypairs(self, user_uuid: UUID) -> int:
        async with self._db.begin() as conn:
            ak_rows = await conn.execute(
                sa.select([keypairs.c.access_key]).where(keypairs.c.user == user_uuid),
            )
            if (row := ak_rows.first()) and (access_key := row.access_key):
                await redis_helper.execute(
                    self._redis_stat,
                    lambda r: r.delete(f"keypair.concurrency_used.{access_key}"),
                )
                await redis_helper.execute(
                    self._redis_stat,
                    lambda r: r.delete(f"keypair.sftp_concurrency_used.{access_key}"),
                )
            result = await conn.execute(
                sa.delete(keypairs).where(keypairs.c.user == user_uuid),
            )
            if result.rowcount > 0:
                log.info("deleted {0} user's keypairs ({1})", result.rowcount, user_uuid)
            return result.rowcount

    async def delete_user_from_db(self, email: str) -> None:
        async with self._db.begin() as conn:
            await conn.execute(sa.delete(users).where(users.c.email == email))

    async def get_kernels_for_monthly_stats(self, user_uuid: Optional[UUID] = None) -> list[Row]:
        time_window = 900
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
            return rows

    async def get_kernel_stats_from_redis(self, kernel_ids: list[str]) -> list[bytes | None]:
        async def _pipe_builder(r: Redis) -> RedisPipeline:
            pipe = r.pipeline()
            for kernel_id in kernel_ids:
                await pipe.get(kernel_id)
            return pipe

        raw_stats = await redis_helper.execute(self._redis_stat, _pipe_builder)
        return raw_stats
