from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.models.session_template import TemplateType
from ai.backend.manager.models.user import UserRole

from .db_source import TemplateDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("TemplateRepository",)

template_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.TEMPLATE_REPOSITORY)),
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


class TemplateRepository:
    _db_source: TemplateDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = TemplateDBSource(db)

    # --- Owner resolution ---

    @template_repository_resilience.apply()
    async def resolve_owner(
        self,
        requester_uuid: uuid.UUID,
        requester_access_key: str,
        requester_role: UserRole,
        requester_domain: str,
        requesting_domain: str,
        requesting_group: str,
        owner_access_key: str | None = None,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        return await self._db_source.resolve_owner(
            requester_uuid,
            requester_access_key,
            requester_role,
            requester_domain,
            requesting_domain,
            requesting_group,
            owner_access_key,
        )

    # --- Task template ---

    @template_repository_resilience.apply()
    async def create_task_templates(
        self,
        domain_name: str,
        items: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        return await self._db_source.create_task_templates(domain_name, items)

    @template_repository_resilience.apply()
    async def list_task_templates(self, user_uuid: uuid.UUID) -> list[dict[str, Any]]:
        return await self._db_source.list_task_templates(user_uuid)

    @template_repository_resilience.apply()
    async def get_task_template(self, template_id: str) -> dict[str, Any] | None:
        return await self._db_source.get_task_template(template_id)

    @template_repository_resilience.apply()
    async def task_template_exists(self, template_id: str) -> bool:
        return await self._db_source.task_template_exists(template_id)

    @template_repository_resilience.apply()
    async def update_task_template(
        self,
        template_id: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        name: str,
        template_data: Mapping[str, Any],
    ) -> int:
        return await self._db_source.update_task_template(
            template_id, group_id, user_uuid, name, template_data
        )

    # --- Cluster template ---

    @template_repository_resilience.apply()
    async def create_cluster_template(
        self,
        domain_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        name: str,
        template_data: Mapping[str, Any],
    ) -> str:
        return await self._db_source.create_cluster_template(
            domain_name, group_id, user_uuid, name, template_data
        )

    @template_repository_resilience.apply()
    async def list_cluster_templates_all(self, user_uuid: uuid.UUID) -> list[dict[str, Any]]:
        return await self._db_source.list_cluster_templates_all(user_uuid)

    @template_repository_resilience.apply()
    async def list_accessible_cluster_templates(
        self,
        user_uuid: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
        allowed_types: Iterable[str],
        group_id_filter: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        return await self._db_source.list_accessible_cluster_templates(
            user_uuid, user_role, domain_name, allowed_types, group_id_filter
        )

    @template_repository_resilience.apply()
    async def get_cluster_template(self, template_id: str) -> dict[str, Any] | None:
        return await self._db_source.get_cluster_template(template_id)

    @template_repository_resilience.apply()
    async def cluster_template_exists(self, template_id: str) -> bool:
        return await self._db_source.cluster_template_exists(template_id)

    @template_repository_resilience.apply()
    async def update_cluster_template(
        self,
        template_id: str,
        template_data: Mapping[str, Any],
        name: str,
    ) -> int:
        return await self._db_source.update_cluster_template(template_id, template_data, name)

    # --- Shared ---

    @template_repository_resilience.apply()
    async def soft_delete_template(self, template_id: str, template_type: TemplateType) -> int:
        return await self._db_source.soft_delete_template(template_id, template_type)
