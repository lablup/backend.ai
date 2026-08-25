"""Database source for auth repository operations."""

from __future__ import annotations

import uuid as uuid_mod
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.exception import BackendAIError, UserNotFound
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.auth.login_session_types import (
    LoginAttemptResult,
    LoginSessionStatus,
)
from ai.backend.manager.data.auth.types import GroupMembershipData, UserCreationData, UserData
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.errors.auth import (
    AuthorizationFailed,
    GroupMembershipNotFoundError,
    LoginSessionNotFoundError,
)
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.errors.user import KeyPairNotFound, UserCreationBadRequest
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import HashInfo, PasswordInfo
from ai.backend.manager.models.keypair.queriers import DefaultKeypairQuerier
from ai.backend.manager.models.keypair.row import generate_keypair_data, keypairs
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.user import (
    UserRole,
    UserRow,
    UserStatus,
    check_credential,
    compare_to_hashed_password,
    users,
)
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.queries import user_scope_membership_exists
from ai.backend.manager.repositories.ops.rbac.provider import FullUserCreation, RBACOpsProvider
from ai.backend.manager.repositories.user.creators import UserScopeCreation
from ai.backend.manager.secret.pool import KeyProviderPool

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


@dataclass(frozen=True)
class ActiveSessionInfo:
    session_token: str
    created_at: datetime


@dataclass(frozen=True)
class LoginSessionCreationResult:
    session_token: str


@dataclass(frozen=True)
class CredentialVerificationResult:
    user: sa.RowMapping
    active_sessions: list[ActiveSessionInfo]  # ordered by created_at ASC


class AuthDBSource:
    """
    Database source for auth operations.
    Handles all database operations for authentication.
    """

    _db: ExtendedAsyncSAEngine
    _rbac_ops_provider: RBACOpsProvider
    _key_provider_pool: KeyProviderPool

    def __init__(self, db: ExtendedAsyncSAEngine, key_provider_pool: KeyProviderPool) -> None:
        self._db = db
        self._rbac_ops_provider = RBACOpsProvider(db)
        self._key_provider_pool = key_provider_pool

    @auth_db_source_resilience.apply()
    async def fetch_group_membership(self, group_id: UUID, user_id: UUID) -> GroupMembershipData:
        """Fetch group membership from database."""
        async with self._db.begin() as conn:
            query = sa.select(user_scope_membership_exists(PROJECT_SCOPE_TYPE, group_id, user_id))
            is_member = (await conn.execute(query)).scalar()
            if not is_member:
                raise GroupMembershipNotFoundError(
                    extra_msg="No such project or you are not the member of it."
                )
        return GroupMembershipData(group_id=group_id, user_id=user_id)

    @auth_db_source_resilience.apply()
    async def verify_email_exists(self, email: str) -> bool:
        """Verify if email exists in the database."""
        async with self._db.begin() as conn:
            query = sa.select(users.c.email).select_from(users).where(users.c.email == email)
            result = await conn.execute(query)
            row = result.first()
            return row is not None

    @auth_db_source_resilience.apply()
    async def fetch_domain_id(self, domain_name: str) -> DomainID:
        """The id of the domain a signup names."""
        async with self._db.begin_readonly() as conn:
            domain_id = await conn.scalar(
                sa.select(DomainRow.id).where(DomainRow.name == domain_name)
            )
        if domain_id is None:
            raise UserCreationBadRequest(f"Domain '{domain_name}' does not exist.")
        return DomainID(domain_id)

    @auth_db_source_resilience.apply()
    async def insert_user_with_keypair(
        self,
        user_spec: UserCreator,
        project_ids: Collection[ProjectID],
        *,
        keypair_resource_policy: str,
        keypair_rate_limit: int,
    ) -> UserCreationData:
        """Provision a signup user in one transaction: the row, its default keypair,
        and its domain/project (model-store included) scope enrollments."""
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.create_full_user(
                FullUserCreation(
                    creation=UserScopeCreation(spec=user_spec),
                    domain_id=user_spec.domain_id,
                    project_ids=project_ids,
                    keypair_resource_policy=keypair_resource_policy,
                    keypair_rate_limit=keypair_rate_limit,
                    keypair_secrets=await generate_keypair_data(self._key_provider_pool),
                )
            )
            return UserCreationData(
                user=self._user_row_to_data(result.user_row),
                keypair=result.keypair,
            )

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
            password_changed_at = result.scalar()
            if password_changed_at is None:
                raise UserNotFound(extra_data={"user_uuid": str(user_uuid)})
            return cast(datetime, password_changed_at)

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
                keypairs.update()
                .values(is_active=False)
                .where(keypairs.c.user.in_(sa.select(users.c.uuid).where(users.c.email == email)))
            )
            await conn.execute(keypair_query)

    @auth_db_source_resilience.apply()
    async def fetch_ssh_public_key(self, access_key: str) -> str | None:
        """Fetch SSH public key for an access key from database."""
        async with self._db.begin() as conn:
            query = sa.select(keypairs.c.ssh_public_key).where(keypairs.c.access_key == access_key)
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

    def _user_row_to_data(self, row: UserRow | sa.Row[Any]) -> UserData:
        """Convert UserRow to UserData."""
        return UserData(
            uuid=row.uuid,
            username=row.username,
            email=row.email,
            password=row.password,
            need_password_change=row.need_password_change or False,
            full_name=row.full_name,
            description=row.description,
            is_active=row.status == UserStatus.ACTIVE,
            status=row.status or UserStatus.ACTIVE,
            status_info=row.status_info,
            created_at=row.created_at,
            modified_at=row.updated_at,
            password_changed_at=row.password_changed_at,
            domain_name=row.domain_name or "",
            role=row.role or UserRole.USER,
            integration_name=row.integration_id,  # DB column is integration_id
            resource_policy=row.resource_policy,
            sudo_session_enabled=row.sudo_session_enabled,
        )

    @auth_db_source_resilience.apply()
    async def fetch_user_info_by_access_key(self, access_key: str) -> tuple[str, UserRole]:
        """Join keypairs→users to get (domain_name, role) for the owner of *access_key*.

        Raises ``ValueError`` if the access key is unknown.
        """
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(users.c.domain_name, users.c.role)
                .select_from(sa.join(keypairs, users, keypairs.c.user == users.c.uuid))
                .where(keypairs.c.access_key == access_key)
            )
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise ValueError("Unknown owner access key")
            return row.domain_name, row.role

    @auth_db_source_resilience.apply()
    async def fetch_user_info_by_email(self, email: str) -> tuple[UUID, UserRole, str]:
        """Fetch (uuid, role, domain_name) for a user identified by *email*.

        Raises ``ValueError`` if the user is not found.
        """
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(users.c.uuid, users.c.role, users.c.domain_name)
                .select_from(users)
                .where(users.c.email == email)
            )
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise ValueError("Cannot delegate an unknown user")
            return row.uuid, row.role, row.domain_name

    @auth_db_source_resilience.apply()
    async def fetch_user_uuid_by_email(self, email: str, domain_name: str) -> UUID | None:
        """Fetch user UUID by email and domain. Returns None if user not found."""
        async with self._db.begin_readonly() as conn:
            return await conn.scalar(
                sa.select(users.c.uuid)
                .select_from(users)
                .where((users.c.email == email) & (users.c.domain_name == domain_name))
            )

    async def _check_password(
        self,
        conn: sa.ext.asyncio.AsyncConnection,
        row: sa.Row[Any],
        target_password_info: PasswordInfo,
    ) -> None:
        """Verify password against stored hash. Raises AuthorizationFailed on mismatch."""
        if row.password is None:
            raise AuthorizationFailed("User credential mismatch.")
        try:
            if not compare_to_hashed_password(target_password_info.password, row.password):
                raise AuthorizationFailed("User credential mismatch.")
        except ValueError:
            raise AuthorizationFailed("User credential mismatch.") from None

    async def _migrate_password_hash(
        self,
        conn: sa.ext.asyncio.AsyncConnection,
        row: sa.Row[Any],
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
    ) -> None:
        """Migrate password hash if the current algorithm differs from the target."""
        current_hash_info = HashInfo.from_hash_string(row.password)
        if target_password_info.need_migration(current_hash_info):
            await conn.execute(
                sa.update(users)
                .where((users.c.email == email) & (users.c.domain_name == domain_name))
                .values(password=target_password_info)
            )

    async def _record_login_history(
        self,
        conn: sa.ext.asyncio.AsyncConnection,
        user_id: UUID,
        domain_name: str,
        result: LoginAttemptResult,
        fail_reason: str | None,
        client_ip: str | None,
    ) -> None:
        """Insert a login history record (internal, within an existing connection)."""
        await conn.execute(
            sa.insert(LoginHistoryRow.__table__).values(
                user_id=user_id,
                domain_name=domain_name,
                result=result,
                fail_reason=fail_reason,
                client_ip=client_ip,
            )
        )

    @auth_db_source_resilience.apply()
    async def record_login_history(
        self,
        user_id: UUID,
        domain_name: str,
        result: LoginAttemptResult,
        fail_reason: str | None = None,
        client_ip: str | None = None,
    ) -> None:
        """Insert a login history record (public, manages its own transaction)."""
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.insert(LoginHistoryRow.__table__).values(
                    user_id=user_id,
                    domain_name=domain_name,
                    result=result,
                    fail_reason=fail_reason,
                    client_ip=client_ip,
                )
            )

    @auth_db_source_resilience.apply()
    async def verify_credential(
        self,
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
        *,
        login_client_type_id: UUID | None = None,
    ) -> CredentialVerificationResult:
        """Verify credentials, migrate password hash, and fetch active sessions.

        When ``login_client_type_id`` is provided, only active sessions of that
        client type are returned so that per-client-type concurrent login
        enforcement works correctly.

        Does NOT record login history — the caller (service layer) handles
        all history recording via try/except.
        """
        async with self._db.connect() as conn:
            result = await conn.execute(
                sa.select(users)
                .select_from(users)
                .where((users.c.email == email) & (users.c.domain_name == domain_name)),
            )
            row = result.first()

            if row is None:
                raise AuthorizationFailed("User credential mismatch.")

            await self._check_password(conn, row, target_password_info)
            await self._migrate_password_hash(conn, row, domain_name, email, target_password_info)

            # Fetch active sessions for the user within the same connection
            session_conditions = (LoginSessionRow.__table__.c.user_id == row.uuid) & (
                LoginSessionRow.__table__.c.status == LoginSessionStatus.ACTIVE
            )
            if login_client_type_id is not None:
                session_conditions = session_conditions & (
                    LoginSessionRow.__table__.c.login_client_type_id == login_client_type_id
                )
            session_result = await conn.execute(
                sa.select(
                    LoginSessionRow.__table__.c.session_token,
                    LoginSessionRow.__table__.c.created_at,
                )
                .where(session_conditions)
                .order_by(LoginSessionRow.__table__.c.created_at.asc())
            )
            active_sessions = [
                ActiveSessionInfo(session_token=r.session_token, created_at=r.created_at)
                for r in session_result
            ]

            await conn.commit()
            return CredentialVerificationResult(
                user=row._mapping,
                active_sessions=active_sessions,
            )

    @auth_db_source_resilience.apply()
    async def delete_sessions_by_tokens(
        self,
        session_tokens: list[str],
        result: LoginAttemptResult,
        client_ip: str | None = None,
    ) -> None:
        """Delete the given login sessions and record history for each.

        Uses a CTE to atomically DELETE + INSERT into login_history with a
        JOIN on users to obtain domain_name.
        """
        if not session_tokens:
            return
        ls = LoginSessionRow.__table__
        lh = LoginHistoryRow.__table__
        async with self._db.connect() as conn:
            deleted = (
                sa.delete(ls)
                .where(ls.c.session_token.in_(session_tokens))
                .returning(ls.c.user_id)
                .cte("deleted")
            )
            insert_query = lh.insert().from_select(
                ["user_id", "domain_name", "result", "client_ip"],
                sa.select(
                    deleted.c.user_id,
                    users.c.domain_name,
                    sa.literal(result.value).label("result"),
                    sa.literal(client_ip, type_=pgsql.INET).label("client_ip"),
                ).select_from(deleted.join(users, deleted.c.user_id == users.c.uuid)),
            )
            await conn.execute(insert_query)
            await conn.commit()

    @auth_db_source_resilience.apply()
    async def create_login_session(
        self,
        user_id: UUID,
        access_key: str,
        domain_name: str,
        *,
        login_client_type_id: UUID | None = None,
        client_ip: str | None = None,
    ) -> LoginSessionCreationResult:
        """Create a new active login session and record a successful login history entry.

        All enforcement (cap check and force-eviction decision) is performed by the
        service layer before this method is called. Eviction of old sessions, when
        needed, must also be performed by the service layer via
        ``invalidate_login_sessions_by_tokens`` prior to this call.
        """
        session_token = uuid_mod.uuid4().hex
        async with self._db.connect() as conn:
            await conn.execute(
                sa.insert(LoginSessionRow.__table__).values(
                    user_id=user_id,
                    access_key=access_key,
                    session_token=session_token,
                    status=LoginSessionStatus.ACTIVE,
                    login_client_type_id=login_client_type_id,
                )
            )

            # Record successful login in the same transaction.
            await self._record_login_history(
                conn,
                user_id,
                domain_name,
                LoginAttemptResult.SUCCESS,
                fail_reason=None,
                client_ip=client_ip,
            )

            await conn.commit()
        return LoginSessionCreationResult(session_token=session_token)

    @auth_db_source_resilience.apply()
    async def verify_credential_without_migration(
        self,
        domain_name: str,
        email: str,
        password: str,
    ) -> sa.RowMapping:
        """Verify credentials without password migration (for signout, etc.)"""
        return await check_credential(
            db=self._db,
            domain=domain_name,
            email=email,
            password=password,
        )

    @auth_db_source_resilience.apply()
    async def fetch_default_keypair(self, user_uuid: UUID) -> KeyPairData:
        """Read the keypair a user authorizes with.

        Every user holding keypairs has one marked, so no mark is a fault rather than
        an answer. An admin creating a keypair for them is the way back.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            if not await db_session.scalar(sa.select(sa.exists().where(UserRow.uuid == user_uuid))):
                raise UserNotFound(extra_data=user_uuid)
            querier = DefaultKeypairQuerier()
            marked = await db_session.scalar(
                querier.build_select().where(querier.owner_id_column() == user_uuid)
            )
            if marked is None:
                raise KeyPairNotFound(f"User {user_uuid} holds no active default keypair")
            return querier.to_data(marked)

    @auth_db_source_resilience.apply()
    async def fetch_current_time(self) -> datetime:
        """Fetch current time from database."""
        async with self._db.begin_readonly() as db_conn:
            result = await db_conn.scalar(sa.select(sa.func.now()))
            if result is None:
                raise InternalServerError("Failed to retrieve current database timestamp")
            return result

    # --- Login Session ---

    @auth_db_source_resilience.apply()
    async def fetch_active_session_tokens(
        self, user_id: UUID, *, login_client_type_id: UUID | None = None
    ) -> list[ActiveSessionInfo]:
        """Fetch active session tokens for a user, ordered by created_at ASC (oldest first).

        When ``login_client_type_id`` is provided, only sessions of that client type
        are returned so that per-client-type concurrent login enforcement works correctly.
        """
        async with self._db.begin_readonly_session() as db_session:
            conditions = (LoginSessionRow.user_id == user_id) & (
                LoginSessionRow.status == LoginSessionStatus.ACTIVE
            )
            if login_client_type_id is not None:
                conditions = conditions & (
                    LoginSessionRow.login_client_type_id == login_client_type_id
                )
            query = (
                sa.select(
                    LoginSessionRow.session_token,
                    LoginSessionRow.created_at,
                )
                .where(conditions)
                .order_by(LoginSessionRow.created_at.asc())
            )
            result = await db_session.execute(query)
            return [
                ActiveSessionInfo(session_token=row.session_token, created_at=row.created_at)
                for row in result
            ]

    @auth_db_source_resilience.apply()
    async def delete_session_by_token(
        self,
        session_token: str,
        result: LoginAttemptResult,
        client_ip: str | None = None,
    ) -> None:
        """Delete a single login session by its token and record history.

        Uses a CTE to atomically DELETE + INSERT into login_history with a
        JOIN on users to obtain domain_name. No-op if the session is not found.
        """
        ls = LoginSessionRow.__table__
        lh = LoginHistoryRow.__table__
        async with self._db.connect() as conn:
            deleted = (
                sa.delete(ls)
                .where(ls.c.session_token == session_token)
                .returning(ls.c.user_id)
                .cte("deleted")
            )
            insert_query = lh.insert().from_select(
                ["user_id", "domain_name", "result", "client_ip"],
                sa.select(
                    deleted.c.user_id,
                    users.c.domain_name,
                    sa.literal(result.value).label("result"),
                    sa.literal(client_ip, type_=pgsql.INET).label("client_ip"),
                ).select_from(deleted.join(users, deleted.c.user_id == users.c.uuid)),
            )
            await conn.execute(insert_query)
            await conn.commit()

    @auth_db_source_resilience.apply()
    async def delete_sessions_by_user(
        self,
        user_id: UUID,
        domain_name: str,
        result: LoginAttemptResult,
        client_ip: str | None = None,
    ) -> list[str]:
        """Delete all login sessions for a user, record history, return tokens.

        The caller provides domain_name (available in signout flow).
        Returns the list of deleted session_tokens for Valkey cleanup.
        """
        ls = LoginSessionRow.__table__
        lh = LoginHistoryRow.__table__
        async with self._db.connect() as conn:
            delete_result = await conn.execute(
                sa.delete(ls).where(ls.c.user_id == user_id).returning(ls.c.session_token)
            )
            deleted_tokens = [row.session_token for row in delete_result]
            if deleted_tokens:
                await conn.execute(
                    sa.insert(lh),
                    [
                        {
                            "user_id": user_id,
                            "domain_name": domain_name,
                            "result": result,
                            "client_ip": client_ip,
                        }
                        for _ in deleted_tokens
                    ],
                )
            await conn.commit()
            return deleted_tokens

    @auth_db_source_resilience.apply()
    async def delete_session_by_id(
        self,
        session_id: UUID,
        result: LoginAttemptResult,
        client_ip: str | None = None,
    ) -> str:
        """Delete a login session by its ID, record history, return session_token.

        Uses a CTE to atomically DELETE + INSERT into login_history with a
        JOIN on users to obtain domain_name.
        Raises LoginSessionNotFoundError if no session is found.
        """
        ls = LoginSessionRow.__table__
        lh = LoginHistoryRow.__table__
        async with self._db.connect() as conn:
            # First, delete and get token + user_id
            delete_result = await conn.execute(
                sa.delete(ls)
                .where(ls.c.id == session_id)
                .returning(ls.c.session_token, ls.c.user_id)
            )
            row = delete_result.first()
            if row is None:
                raise LoginSessionNotFoundError(
                    extra_msg=f"No login session found with id: {session_id}"
                )
            session_token: str = row.session_token
            # Get domain_name from users table
            user_result = await conn.execute(
                sa.select(users.c.domain_name).where(users.c.uuid == row.user_id)
            )
            domain_name = user_result.scalar_one()
            # Record history
            await conn.execute(
                sa.insert(lh).values(
                    user_id=row.user_id,
                    domain_name=domain_name,
                    result=result,
                    client_ip=client_ip,
                )
            )
            await conn.commit()
            return session_token
