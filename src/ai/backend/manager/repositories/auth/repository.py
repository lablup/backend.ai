from datetime import datetime
from typing import Optional
from uuid import UUID

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.auth.types import GroupMembershipData, UserData
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.auth.db_source.db_source import AuthDBSource

auth_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.AUTH_REPOSITORY)),
    ]
)


class AuthRepository:
    _db_source: AuthDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AuthDBSource(db)

    @auth_repository_resilience.apply()
    async def get_group_membership(self, group_id: UUID, user_id: UUID) -> GroupMembershipData:
        return await self._db_source.fetch_group_membership(group_id, user_id)

    @auth_repository_resilience.apply()
    async def check_email_exists(self, email: str) -> bool:
        return await self._db_source.verify_email_exists(email)

    @auth_repository_resilience.apply()
    async def create_user_with_keypair(
        self,
        user_data: dict,
        keypair_data: dict,
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
    async def get_ssh_public_key(self, access_key: str) -> Optional[str]:
        return await self._db_source.fetch_ssh_public_key(access_key)

    @auth_repository_resilience.apply()
    async def update_ssh_keypair(self, access_key: str, public_key: str, private_key: str) -> None:
        await self._db_source.modify_ssh_keypair(access_key, public_key, private_key)

    @auth_repository_resilience.apply()
    async def check_credential_with_migration(
        self,
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
    ) -> dict:
        return await self._db_source.verify_credential_with_migration(
            domain_name, email, target_password_info
        )

    @auth_repository_resilience.apply()
    async def check_credential_without_migration(
        self,
        domain_name: str,
        email: str,
        password: str,
    ) -> dict:
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
