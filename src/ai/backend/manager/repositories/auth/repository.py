import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.auth.login_session_types import LoginHistoryData, LoginSessionData
from ai.backend.manager.data.auth.types import GroupMembershipData, UserData
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.auth.db_source.db_source import (
    AuthDBSource,
    CredentialVerificationResult,
    LoginSessionCreationResult,
)
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.types import SearchScope

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

auth_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.AUTH_REPOSITORY)),
    ]
)


class AuthRepository:
    _db_source: AuthDBSource
    _valkey_session_client: ValkeySessionClient

    def __init__(
        self, db: ExtendedAsyncSAEngine, valkey_session_client: ValkeySessionClient
    ) -> None:
        self._db_source = AuthDBSource(db)
        self._valkey_session_client = valkey_session_client

    async def _delete_valkey_sessions(self, session_tokens: list[str]) -> None:
        """Delete Valkey session keys for the given session tokens.

        Valkey errors are caught and logged — they must not roll back DB transactions.
        """
        if not session_tokens:
            return
        keys = [f"AIOHTTP_SESSION_{t}" for t in session_tokens]
        try:
            await self._valkey_session_client.delete_session_data_batch(keys)
        except Exception:
            log.exception("Failed to delete Valkey session keys; DB transaction is unaffected")

    @auth_repository_resilience.apply()
    async def get_group_membership(self, group_id: UUID, user_id: UUID) -> GroupMembershipData:
        return await self._db_source.fetch_group_membership(group_id, user_id)

    @auth_repository_resilience.apply()
    async def check_email_exists(self, email: str) -> bool:
        return await self._db_source.verify_email_exists(email)

    @auth_repository_resilience.apply()
    async def create_user_with_keypair(
        self,
        user_data: dict[str, Any],
        keypair_data: dict[str, Any],
        group_name: str,
        domain_name: str,
    ) -> UserData:
        return await self._db_source.insert_user_with_keypair(
            user_data, keypair_data, group_name, domain_name
        )

    @auth_repository_resilience.apply()
    async def update_user_full_name(self, email: str, domain_name: str, full_name: str) -> None:
        await self._db_source.modify_user_full_name(email, domain_name, full_name)

    @auth_repository_resilience.apply()
    async def update_user_password(self, email: str, password_info: PasswordInfo) -> None:
        await self._db_source.modify_user_password(email, password_info)

    @auth_repository_resilience.apply()
    async def update_user_password_by_uuid(
        self, user_uuid: UUID, password_info: PasswordInfo
    ) -> datetime:
        return await self._db_source.modify_user_password_by_uuid(user_uuid, password_info)

    @auth_repository_resilience.apply()
    async def deactivate_user_and_keypairs(self, email: str) -> None:
        await self._db_source.mark_user_and_keypairs_inactive(email)

    @auth_repository_resilience.apply()
    async def get_ssh_public_key(self, access_key: str) -> str | None:
        return await self._db_source.fetch_ssh_public_key(access_key)

    @auth_repository_resilience.apply()
    async def update_ssh_keypair(self, access_key: str, public_key: str, private_key: str) -> None:
        await self._db_source.modify_ssh_keypair(access_key, public_key, private_key)

    @auth_repository_resilience.apply()
    async def get_delegation_target_by_access_key(self, access_key: str) -> tuple[str, UserRole]:
        return await self._db_source.fetch_user_info_by_access_key(access_key)

    @auth_repository_resilience.apply()
    async def get_delegation_target_by_email(self, email: str) -> tuple[UUID, UserRole, str]:
        return await self._db_source.fetch_user_info_by_email(email)

    @auth_repository_resilience.apply()
    async def check_credential_with_migration(
        self,
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
        *,
        force: bool = False,
        max_session_age: int = 604800,
    ) -> CredentialVerificationResult:
        result = await self._db_source.verify_credential_with_migration(
            domain_name,
            email,
            target_password_info,
            force=force,
            max_session_age=max_session_age,
        )
        await self._delete_valkey_sessions(result.invalidated_session_tokens)
        return result

    @auth_repository_resilience.apply()
    async def create_login_session(
        self,
        user_id: UUID,
        access_key: str,
        max_session_age: int = 604800,
    ) -> LoginSessionCreationResult:
        return await self._db_source.create_login_session(user_id, access_key, max_session_age)

    @auth_repository_resilience.apply()
    async def check_credential_without_migration(
        self,
        domain_name: str,
        email: str,
        password: str,
    ) -> sa.RowMapping:
        """Check credentials without password migration (for signout, etc.)"""
        return await self._db_source.verify_credential_without_migration(
            domain_name, email, password
        )

    @auth_repository_resilience.apply()
    async def get_user_row_by_uuid(self, user_uuid: UUID) -> UserRow:
        return await self._db_source.fetch_user_row_by_uuid(user_uuid)

    @auth_repository_resilience.apply()
    async def get_current_time(self) -> datetime:
        return await self._db_source.fetch_current_time()

    # --- Login Session ---

    @auth_repository_resilience.apply()
    async def invalidate_login_session_by_token(self, session_token: str) -> None:
        await self._db_source.invalidate_session_by_token(session_token)
        await self._delete_valkey_sessions([session_token])

    @auth_repository_resilience.apply()
    async def invalidate_user_login_sessions(self, user_id: UUID) -> None:
        tokens = await self._db_source.invalidate_sessions_by_user(user_id)
        await self._delete_valkey_sessions(tokens)

    @auth_repository_resilience.apply()
    async def search_login_sessions(
        self,
        scope: SearchScope,
        querier: BatchQuerier,
    ) -> SearchResult[LoginSessionData]:
        return await self._db_source.search_login_sessions(scope, querier)

    # --- Login History ---

    @auth_repository_resilience.apply()
    async def search_login_history(
        self,
        scope: SearchScope,
        querier: BatchQuerier,
    ) -> SearchResult[LoginHistoryData]:
        return await self._db_source.search_login_history(scope, querier)
