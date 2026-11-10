from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.session_template.types import (
    SessionTemplateData,
    SessionTemplateWithOwnerEmailAndProjectName,
    TemplateType,
)
from ai.backend.manager.models.session_template.scopes import SessionTemplateTarget
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.template.db_source.db_source import TemplateDBSource

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

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: ShareOpsProvider) -> None:
        self._db_source = TemplateDBSource(db, ops_provider)

    # --- Owner resolution ---

    @template_repository_resilience.apply()
    async def resolve_owner(
        self,
        requester_uuid: UserID,
        requester_access_key: str,
        requester_role: UserRole,
        requester_domain: str,
        requesting_domain: str,
        requesting_project_id: ProjectID,
        owner_access_key: str | None = None,
    ) -> tuple[UserID, ProjectID]:
        return await self._db_source.resolve_owner(
            requester_uuid,
            requester_access_key,
            requester_role,
            requester_domain,
            requesting_domain,
            requesting_project_id,
            owner_access_key,
        )

    # --- Task template ---

    @template_repository_resilience.apply()
    async def create_task_templates(
        self,
        domain_name: str,
        items: list[dict[str, Any]],
    ) -> None:
        await self._db_source.create_task_templates(domain_name, items)

    @template_repository_resilience.apply()
    async def get_task_template(self, template_id: SessionTemplateID) -> SessionTemplateData | None:
        return await self._db_source.get_task_template(template_id)

    @template_repository_resilience.apply()
    async def task_template_exists(self, template_id: SessionTemplateID) -> bool:
        return await self._db_source.task_template_exists(template_id)

    @template_repository_resilience.apply()
    async def update_task_template(
        self,
        template_id: SessionTemplateID,
        group_id: ProjectID,
        user_uuid: UserID,
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
        group_id: ProjectID,
        user_uuid: UserID,
        name: str,
        template_data: Mapping[str, Any],
    ) -> SessionTemplateID:
        return await self._db_source.create_cluster_template(
            domain_name, group_id, user_uuid, name, template_data
        )

    @template_repository_resilience.apply()
    async def joined_project_ids(self, user_id: UserID) -> list[ProjectID]:
        return await self._db_source.joined_project_ids(user_id)

    @template_repository_resilience.apply()
    async def list_templates_in_scopes(
        self,
        template_type: TemplateType,
        scopes: Sequence[SessionTemplateTarget],
        group_id_filter: ProjectID | None,
    ) -> list[SessionTemplateWithOwnerEmailAndProjectName]:
        return await self._db_source.list_templates_in_scopes(
            template_type, scopes, group_id_filter
        )

    @template_repository_resilience.apply()
    async def list_templates_in_global(
        self, template_type: TemplateType
    ) -> list[SessionTemplateWithOwnerEmailAndProjectName]:
        return await self._db_source.list_templates_in_global(template_type)

    @template_repository_resilience.apply()
    async def get_cluster_template(
        self, template_id: SessionTemplateID
    ) -> SessionTemplateData | None:
        return await self._db_source.get_cluster_template(template_id)

    @template_repository_resilience.apply()
    async def cluster_template_exists(self, template_id: SessionTemplateID) -> bool:
        return await self._db_source.cluster_template_exists(template_id)

    @template_repository_resilience.apply()
    async def update_cluster_template(
        self,
        template_id: SessionTemplateID,
        template_data: Mapping[str, Any],
        name: str,
    ) -> int:
        return await self._db_source.update_cluster_template(template_id, template_data, name)

    # --- Shared ---

    @template_repository_resilience.apply()
    async def soft_delete_template(
        self, template_id: SessionTemplateID, template_type: TemplateType
    ) -> int:
        return await self._db_source.soft_delete_template(template_id, template_type)
