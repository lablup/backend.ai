from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.dotfile.types import DotfileQueryResult

from .db_source import DotfileDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("DotfileRepository",)

dotfile_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.DOTFILE_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class DotfileRepository:
    _db_source: DotfileDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = DotfileDBSource(db)

    # --- Domain dotfiles ---

    @dotfile_repository_resilience.apply()
    async def get_domain_dotfiles(self, domain_name: str) -> DotfileQueryResult:
        return await self._db_source.get_domain_dotfiles(domain_name)

    @dotfile_repository_resilience.apply()
    async def save_domain_dotfiles(self, domain_name: str, packed: bytes) -> None:
        await self._db_source.save_domain_dotfiles(domain_name, packed)

    # --- Group dotfiles ---

    @dotfile_repository_resilience.apply()
    async def get_group_dotfiles(self, group_id: uuid.UUID) -> DotfileQueryResult:
        return await self._db_source.get_group_dotfiles(group_id)

    @dotfile_repository_resilience.apply()
    async def save_group_dotfiles(self, group_id: uuid.UUID, packed: bytes) -> None:
        await self._db_source.save_group_dotfiles(group_id, packed)

    # --- User dotfiles ---

    @dotfile_repository_resilience.apply()
    async def get_user_dotfiles(self, access_key: str) -> DotfileQueryResult:
        return await self._db_source.get_user_dotfiles(access_key)

    @dotfile_repository_resilience.apply()
    async def save_user_dotfiles(self, access_key: str, packed: bytes) -> None:
        await self._db_source.save_user_dotfiles(access_key, packed)

    # --- vFolder conflict check ---

    @dotfile_repository_resilience.apply()
    async def check_vfolder_conflict(self, user_uuid: uuid.UUID, path: str) -> bool:
        return await self._db_source.check_vfolder_conflict(user_uuid, path)

    # --- Group resolution ---

    @dotfile_repository_resilience.apply()
    async def resolve_group(
        self,
        group_id_or_name: str | uuid.UUID,
        group_domain: str | None,
        user_domain: str,
    ) -> tuple[UUID | None, str | None]:
        return await self._db_source.resolve_group(group_id_or_name, group_domain, user_domain)

    # --- Group membership ---

    @dotfile_repository_resilience.apply()
    async def get_user_group_ids(self, user_uuid: uuid.UUID) -> list[uuid.UUID]:
        return await self._db_source.get_user_group_ids(user_uuid)

    # --- Bootstrap script ---

    @dotfile_repository_resilience.apply()
    async def get_bootstrap_script(self, access_key: str) -> tuple[str, int]:
        return await self._db_source.get_bootstrap_script(access_key)

    @dotfile_repository_resilience.apply()
    async def save_bootstrap_script(self, access_key: str, script: str) -> None:
        await self._db_source.save_bootstrap_script(access_key, script)
