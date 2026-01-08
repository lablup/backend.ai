"""Database source for auth repository operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload

from ai.backend.common.exception import BackendAIError, UserNotFound
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.auth.types import GroupMembershipData, UserData
from ai.backend.manager.errors.auth import GroupMembershipNotFoundError, UserCreationError
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

auth_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.AUTH_DB_SOURCE)),
        RetryPolicy(
            RetryArgs(
                max_retries=5,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class AuthDBSource:
    """
    Database source for auth operations.
    Handles all database operations for authentication.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @auth_db_source_resilience.apply()
    async def fetch_group_membership(self, group_id: UUID, user_id: UUID) -> GroupMembershipData:
        """Fetch group membership from database."""
        async with self._db.begin() as conn:
            query = (
                sa.select([association_groups_users.c.group_id, association_groups_users.c.user_id])
                .select_from(association_groups_users)
                .where(
                    (association_groups_users.c.group_id == group_id)
                    & (association_groups_users.c.user_id == user_id)
                )
            )
            result = await conn.execute(query)
            row = result.first()
            if not row:
                raise GroupMembershipNotFoundError(
                    extra_msg="No such project or you are not the member of it."
                )
        return GroupMembershipData(group_id=row.group_id, user_id=row.user_id)

    @auth_db_source_resilience.apply()
    async def verify_email_exists(self, email: str) -> bool:
        """Verify if email exists in the database."""
        async with self._db.begin() as conn:
            query = sa.select([users.c.email]).select_from(users).where(users.c.email == email)
            result = await conn.execute(query)
            row = result.first()
            return row is not None

    @auth_db_source_resilience.apply()
    async def insert_user_with_keypair(
        self,
        user_data: dict,
        keypair_data: dict,
        group_name: str,
        domain_name: str,
    ) -> UserData:
        """Insert a new user with keypair and add to default group in database."""
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

    @auth_db_source_resilience.apply()
    async def modify_user_full_name(self, email: str, domain_name: str, full_name: str) -> None:
        """Modify user's full name in database."""
        async with self._db.begin() as conn:
            query = (
                sa.select(users)
                .select_from(users)
                .where((users.c.email == email) & (users.c.domain_name == domain_name))
            )
            result = await conn.execute(query)
            user_row = result.first()
            if not user_row:
                raise UserNotFound(extra_data={"email": email, "domain": domain_name})

            data = {"full_name": full_name}
            update_query = users.update().values(data).where(users.c.email == email)
            await conn.execute(update_query)

    @auth_db_source_resilience.apply()
    async def modify_user_password(self, email: str, password_info: PasswordInfo) -> None:
        """Modify user's password in database."""
        async with self._db.begin() as conn:
            data = {
                "password": password_info,  # PasswordColumn will handle the conversion
                "need_password_change": False,
                "password_changed_at": sa.func.now(),
            }
            query = users.update().values(data).where(users.c.email == email)
            await conn.execute(query)

    @auth_db_source_resilience.apply()
    async def modify_user_password_by_uuid(
        self, user_uuid: UUID, password_info: PasswordInfo
    ) -> datetime:
        """Modify user's password by UUID in database and return the password_changed_at timestamp."""
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

    @auth_db_source_resilience.apply()
    async def mark_user_and_keypairs_inactive(self, email: str) -> None:
        """Mark user and all their keypairs as inactive in database."""
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

    @auth_db_source_resilience.apply()
    async def fetch_ssh_public_key(self, access_key: str) -> Optional[str]:
        """Fetch SSH public key for an access key from database."""
        async with self._db.begin() as conn:
            query = sa.select([keypairs.c.ssh_public_key]).where(
                keypairs.c.access_key == access_key
            )
            return await conn.scalar(query)

    @auth_db_source_resilience.apply()
    async def modify_ssh_keypair(self, access_key: str, public_key: str, private_key: str) -> None:
        """Modify SSH keypair for an access key in database."""
        async with self._db.begin() as conn:
            data = {
                "ssh_public_key": public_key,
                "ssh_private_key": private_key,
            }
            query = keypairs.update().values(data).where(keypairs.c.access_key == access_key)
            await conn.execute(query)

    def _user_row_to_data(self, row: UserRow) -> UserData:
        """Convert UserRow to UserData."""
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

    @auth_db_source_resilience.apply()
    async def verify_credential_with_migration(
        self,
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
    ) -> dict[str, Any]:
        """Verify credentials with password migration support."""
        return await check_credential_with_migration(
            db=self._db,
            domain=domain_name,
            email=email,
            target_password_info=target_password_info,
        )

    @auth_db_source_resilience.apply()
    async def verify_credential_without_migration(
        self,
        domain_name: str,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        """Verify credentials without password migration (for signout, etc.)"""
        return await check_credential(
            db=self._db,
            domain=domain_name,
            email=email,
            password=password,
        )

    @auth_db_source_resilience.apply()
    async def fetch_user_row_by_uuid(self, user_uuid: UUID) -> UserRow:
        """Fetch user row by UUID from database."""
        async with self._db.begin_session() as db_session:
            user_query = (
                sa.select(UserRow)
                .where(UserRow.uuid == user_uuid)
                .options(
                    joinedload(UserRow.main_keypair),
                    selectinload(UserRow.keypairs),
                )
            )
            user_row = await db_session.scalar(user_query)
            if user_row is None:
                raise UserNotFound(extra_data=user_uuid)
            return user_row

    @auth_db_source_resilience.apply()
    async def fetch_current_time(self) -> datetime:
        """Fetch current time from database."""
        async with self._db.begin_readonly() as db_conn:
            return await db_conn.scalar(sa.select(sa.func.now()))
