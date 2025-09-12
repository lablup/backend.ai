from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.auth.types import GroupMembershipData, UserData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.auth import (
    GroupMembershipNotFoundError,
    UserCreationError,
)
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import (
    UserRow,
    UserStatus,
    check_credential,
    check_credential_with_migration,
    users,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for auth repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.AUTH)


class AuthRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_user_by_email_validated(self, email: str, domain_name: str) -> Optional[UserData]:
        async with self._db.begin() as conn:
            row = await self._get_user_by_email(conn, email, domain_name)
            if not row:
                return None
            return self._user_row_to_data(row)

    async def _get_user_by_email(
        self, session: SASession, email: str, domain_name: str
    ) -> Optional[UserRow]:
        query = (
            sa.select(users)
            .select_from(users)
            .where((users.c.email == email) & (users.c.domain_name == domain_name))
        )
        result = await session.execute(query)
        return result.first()

    @repository_decorator()
    async def get_group_membership_validated(
        self, group_id: UUID, user_id: UUID
    ) -> GroupMembershipData:
        async with self._db.begin() as conn:
            membership = await self._get_group_membership(conn, group_id, user_id)
            if not membership:
                raise GroupMembershipNotFoundError(
                    extra_msg="No such project or you are not the member of it."
                )
            return membership

    async def _get_group_membership(
        self, session: SASession, group_id: UUID, user_id: UUID
    ) -> Optional[GroupMembershipData]:
        query = (
            sa.select([association_groups_users.c.group_id, association_groups_users.c.user_id])
            .select_from(association_groups_users)
            .where(
                (association_groups_users.c.group_id == group_id)
                & (association_groups_users.c.user_id == user_id)
            )
        )
        result = await session.execute(query)
        row = result.first()
        if not row:
            return None
        return GroupMembershipData(group_id=row.group_id, user_id=row.user_id)

    @repository_decorator()
    async def check_email_exists(self, email: str) -> bool:
        async with self._db.begin() as conn:
            query = sa.select([users.c.email]).select_from(users).where(users.c.email == email)
            result = await conn.execute(query)
            row = result.first()
            return row is not None

    @repository_decorator()
    async def create_user_with_keypair(
        self,
        user_data: dict,
        keypair_data: dict,
        group_name: str,
        domain_name: str,
    ) -> UserData:
        async with self._db.begin() as conn:
            # Create user
            query = users.insert().values(user_data)
            result = await conn.execute(query)
            if result.rowcount == 0:
                raise UserCreationError("Failed to create user")

            # Get created user
            user_query = users.select().where(users.c.email == user_data["email"])
            result = await conn.execute(user_query)
            user_row = result.first()

            # Create keypair
            keypair_data["user"] = user_row.uuid
            keypair_query = keypairs.insert().values(keypair_data)
            await conn.execute(keypair_query)

            # Add to default group
            group_query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where((groups.c.domain_name == domain_name) & (groups.c.name == group_name))
            )
            result = await conn.execute(group_query)
            grp = result.first()
            if grp is not None:
                values = [{"user_id": user_row.uuid, "group_id": grp.id}]
                assoc_query = association_groups_users.insert().values(values)
                await conn.execute(assoc_query)

            return self._user_row_to_data(user_row)

    @repository_decorator()
    async def update_user_full_name_validated(
        self, email: str, domain_name: str, full_name: str
    ) -> bool:
        async with self._db.begin() as conn:
            user_row = await self._get_user_by_email(conn, email, domain_name)
            if not user_row:
                return False

            data = {"full_name": full_name}
            update_query = users.update().values(data).where(users.c.email == email)
            await conn.execute(update_query)
            return True

    @repository_decorator()
    async def update_user_password_validated(self, email: str, password_info: PasswordInfo) -> None:
        async with self._db.begin() as conn:
            data = {
                "password": password_info,  # PasswordColumn will handle the conversion
                "need_password_change": False,
                "password_changed_at": sa.func.now(),
            }
            query = users.update().values(data).where(users.c.email == email)
            await conn.execute(query)

    @repository_decorator()
    async def update_user_password_by_uuid_validated(
        self, user_uuid: UUID, password_info: PasswordInfo
    ) -> datetime:
        async with self._db.begin() as conn:
            data = {
                "password": password_info,  # PasswordColumn will handle the conversion
                "need_password_change": False,
                "password_changed_at": sa.func.now(),
            }
            query = (
                sa.update(users)
                .values(data)
                .where(users.c.uuid == user_uuid)
                .returning(users.c.password_changed_at)
            )
            result = await conn.execute(query)
            return result.scalar()

    @repository_decorator()
    async def deactivate_user_and_keypairs_validated(self, email: str) -> None:
        async with self._db.begin() as conn:
            # Deactivate user
            user_query = (
                users.update().values(status=UserStatus.INACTIVE).where(users.c.email == email)
            )
            await conn.execute(user_query)

            # Deactivate keypairs
            keypair_query = (
                keypairs.update().values(is_active=False).where(keypairs.c.user_id == email)
            )
            await conn.execute(keypair_query)

    @repository_decorator()
    async def get_ssh_public_key_validated(self, access_key: str) -> Optional[str]:
        async with self._db.begin() as conn:
            query = sa.select([keypairs.c.ssh_public_key]).where(
                keypairs.c.access_key == access_key
            )
            return await conn.scalar(query)

    @repository_decorator()
    async def update_ssh_keypair_validated(
        self, access_key: str, public_key: str, private_key: str
    ) -> None:
        async with self._db.begin() as conn:
            data = {
                "ssh_public_key": public_key,
                "ssh_private_key": private_key,
            }
            query = keypairs.update().values(data).where(keypairs.c.access_key == access_key)
            await conn.execute(query)

    def _user_row_to_data(self, row: UserRow) -> UserData:
        return UserData(
            uuid=row.uuid,
            username=row.username,
            email=row.email,
            password=row.password,
            need_password_change=row.need_password_change,
            full_name=row.full_name,
            description=row.description,
            is_active=row.status == UserStatus.ACTIVE,
            status=row.status,
            status_info=row.status_info,
            created_at=row.created_at,
            modified_at=row.modified_at,
            password_changed_at=row.password_changed_at,
            domain_name=row.domain_name,
            role=row.role,
            integration_id=row.integration_id,
            resource_policy=row.resource_policy,
            sudo_session_enabled=row.sudo_session_enabled,
        )

    @repository_decorator()
    async def check_credential_with_migration(
        self,
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
    ) -> Optional[dict]:
        return await check_credential_with_migration(
            db=self._db,
            domain=domain_name,
            email=email,
            target_password_info=target_password_info,
        )

    @repository_decorator()
    async def check_credential_without_migration(
        self,
        domain_name: str,
        email: str,
        password: str,
    ) -> Optional[dict]:
        """Check credentials without password migration (for signout, etc.)"""
        return await check_credential(
            db=self._db,
            domain=domain_name,
            email=email,
            password=password,
        )

    @repository_decorator()
    async def get_user_row_by_uuid_validated(self, user_uuid) -> Optional[UserRow]:
        async with self._db.begin_session() as db_session:
            return await UserRow.query_user_by_uuid(user_uuid, db_session)

    @repository_decorator()
    async def get_current_time_validated(self) -> datetime:
        async with self._db.begin_readonly() as db_conn:
            return await db_conn.scalar(sa.select(sa.func.now()))
