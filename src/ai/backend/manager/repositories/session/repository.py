from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm.strategy_options import _AbstractLoad

from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import AccessKey, ImageAlias, SessionId
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelListResult
from ai.backend.manager.data.session.types import SessionListResult
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.session.db_source import SessionDBSource

session_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SESSION_REPOSITORY)),
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


class SessionRepository:
    _db_source: SessionDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = SessionDBSource(db)

    @session_repository_resilience.apply()
    async def get_session_owner(self, session_id: str | SessionId) -> UserData:
        return await self._db_source.get_session_owner(session_id)

    @session_repository_resilience.apply()
    async def get_session_validated(
        self,
        session_name_or_id: str | SessionId,
        owner_access_key: AccessKey,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        allow_stale: bool = False,
        eager_loading_op: Sequence[_AbstractLoad] | None = None,
    ) -> SessionRow:
        return await self._db_source.get_session_validated(
            session_name_or_id,
            owner_access_key,
            kernel_loading_strategy,
            allow_stale,
            eager_loading_op,
        )

    @session_repository_resilience.apply()
    async def match_sessions(
        self,
        id_or_name_prefix: str,
        owner_access_key: AccessKey,
    ) -> list[SessionRow]:
        return await self._db_source.match_sessions(id_or_name_prefix, owner_access_key)

    @session_repository_resilience.apply()
    async def get_session_to_determine_status(
        self,
        session_id: SessionId,
    ) -> SessionRow:
        return await self._db_source.get_session_to_determine_status(session_id)

    @session_repository_resilience.apply()
    async def get_template_by_id(
        self,
        template_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        return await self._db_source.get_template_by_id(template_id)

    @session_repository_resilience.apply()
    async def get_template_info_by_id(
        self,
        template_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        return await self._db_source.get_template_info_by_id(template_id)

    @session_repository_resilience.apply()
    async def update_session_name(
        self,
        session_name_or_id: str | SessionId,
        new_name: str,
        owner_access_key: AccessKey,
    ) -> SessionRow:
        return await self._db_source.update_session_name(
            session_name_or_id, new_name, owner_access_key
        )

    @session_repository_resilience.apply()
    async def get_container_registry(
        self,
        registry_hostname: str,
        registry_project: str,
    ) -> ContainerRegistryRow | None:
        return await self._db_source.get_container_registry(registry_hostname, registry_project)

    @session_repository_resilience.apply()
    async def resolve_image(
        self,
        image_identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
        alive_only: bool = True,
    ) -> ImageRow:
        """Resolve an image from the given identifiers.

        When ``alive_only`` is True (default), only images with the ALIVE status
        are considered.  Set it to False to also include DELETED images, which is
        useful when the caller needs to reference images that are no longer active
        (e.g., committing a session whose base image has been deleted).
        """
        return await self._db_source.resolve_image(image_identifiers, alive_only)

    @session_repository_resilience.apply()
    async def get_customized_image_count(
        self,
        image_visibility: str,
        image_owner_id: str,
    ) -> int:
        return await self._db_source.get_customized_image_count(image_visibility, image_owner_id)

    @session_repository_resilience.apply()
    async def get_existing_customized_image(
        self,
        new_canonical: str,
        image_visibility: str,
        image_owner_id: str,
        image_name: str,
    ) -> ImageRow | None:
        return await self._db_source.get_existing_customized_image(
            new_canonical, image_visibility, image_owner_id, image_name
        )

    @session_repository_resilience.apply()
    async def get_group_name_by_domain_and_id(
        self,
        domain_name: str,
        group_id: uuid.UUID,
    ) -> str | None:
        return await self._db_source.get_group_name_by_domain_and_id(domain_name, group_id)

    @session_repository_resilience.apply()
    async def get_scaling_group_wsproxy_addr(
        self,
        scaling_group_name: str,
    ) -> str | None:
        return await self._db_source.get_scaling_group_wsproxy_addr(scaling_group_name)

    @session_repository_resilience.apply()
    async def get_session_by_id(
        self,
        session_id: str | SessionId,
    ) -> SessionRow | None:
        return await self._db_source.get_session_by_id(session_id)

    @session_repository_resilience.apply()
    async def modify_session(
        self,
        updater: Updater[SessionRow],
        session_name: str | None = None,
    ) -> SessionRow | None:
        return await self._db_source.modify_session(updater, session_name)

    @session_repository_resilience.apply()
    async def query_userinfo(
        self,
        user_id: uuid.UUID,
        requester_access_key: AccessKey,
        user_role: UserRole,
        domain_name: str,
        keypair_resource_policy: dict[str, Any] | None,
        query_domain_name: str,
        group_name: str | None,
        query_on_behalf_of: AccessKey | None = None,
    ) -> tuple[uuid.UUID, uuid.UUID, dict[str, Any]]:
        return await self._db_source.query_userinfo(
            user_id,
            requester_access_key,
            user_role,
            domain_name,
            keypair_resource_policy,
            query_domain_name,
            group_name,
            query_on_behalf_of,
        )

    @session_repository_resilience.apply()
    async def get_target_session_ids(
        self,
        session_name_or_id: str | uuid.UUID,
        access_key: AccessKey,
        recursive: bool = False,
    ) -> list[SessionId]:
        """
        Get list of session IDs including dependent sessions if recursive.

        :param session_name_or_id: Name or ID of the primary session
        :param access_key: Access key of the session owner
        :param recursive: If True, include dependent sessions
        :return: List of session IDs
        """
        return await self._db_source.get_target_session_ids(
            session_name_or_id, access_key, recursive
        )

    @session_repository_resilience.apply()
    async def find_dependency_sessions(
        self,
        session_name_or_id: uuid.UUID | str,
        access_key: AccessKey,
    ) -> dict[str, list[Any] | str]:
        return await self._db_source.find_dependency_sessions(session_name_or_id, access_key)

    @session_repository_resilience.apply()
    async def get_session_with_group(
        self,
        session_name_or_id: str | SessionId,
        owner_access_key: AccessKey,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        allow_stale: bool = False,
    ) -> SessionRow:
        """Get session with group information eagerly loaded"""
        return await self._db_source.get_session_with_group(
            session_name_or_id, owner_access_key, kernel_loading_strategy, allow_stale
        )

    @session_repository_resilience.apply()
    async def get_session_with_routing_minimal(
        self,
        session_name_or_id: str | SessionId,
        owner_access_key: AccessKey,
    ) -> SessionRow:
        """Get session with minimal routing information"""
        return await self._db_source.get_session_with_routing_minimal(
            session_name_or_id, owner_access_key
        )

    @session_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> SessionListResult:
        """Search sessions with querier pattern.

        Args:
            querier: BatchQuerier for filtering, ordering, and pagination

        Returns:
            SessionListResult with items, total count, and pagination info
        """
        return await self._db_source.search(querier)

    @session_repository_resilience.apply()
    async def search_kernels(
        self,
        querier: BatchQuerier,
    ) -> KernelListResult:
        """Search kernels with querier pattern.

        Args:
            querier: BatchQuerier for filtering, ordering, and pagination

        Returns:
            KernelListResult with items, total count, and pagination info
        """
        return await self._db_source.search_kernels(querier)
