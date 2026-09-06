import logging
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryData,
    ContainerRegistrySearchResult,
)
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.image import (
    ContainerRegistryGroupsAssociationNotFound,
    ContainerRegistryNotFound,
)
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ai.backend.manager.models.container_registry.creators import (
    ContainerRegistryCreator,
    ContainerRegistryProjectCreator,
)
from ai.backend.manager.models.container_registry.purgers import (
    ContainerRegistryProjectPurger,
    ContainerRegistryPurger,
)
from ai.backend.manager.models.container_registry.updaters import ContainerRegistryUpdater
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.querier import (
    BatchQuerier,
    execute_batch_querier,
)
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.write import V2RelationWriteOps

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

container_registry_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.CONTAINER_REGISTRY_REPOSITORY)
        ),
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


class ContainerRegistryRepository:
    _db: ExtendedAsyncSAEngine
    _ops_provider: RelationOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: RelationOpsProvider) -> None:
        self._db = db
        self._ops_provider = ops_provider

    async def create_registry(
        self,
        creator: ContainerRegistryCreator,
    ) -> ContainerRegistryData:
        """Create a container registry with its own virtual entity, related to the
        allowed projects."""
        allowed_groups = creator.allowed_groups
        async with self._ops_provider.write_ops() as w:
            data = await w.create_global_entity(creator)
            if allowed_groups is not None and allowed_groups.add:
                await self._handle_allowed_groups_update(w, data.id, allowed_groups)
            return data

    async def modify_registry(
        self,
        updater: ContainerRegistryUpdater,
    ) -> ContainerRegistryData:
        registry_id = updater.registry_id
        async with self._ops_provider.write_ops() as w:
            if updater.has_allowed_groups_update:
                await self._handle_allowed_groups_update(
                    w, registry_id, updater.allowed_groups.value()
                )

            data = await w.update_data(updater)
            if data is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")
            if updater.build_values():
                ContainerRegistryValidator(
                    ContainerRegistryValidatorArgs(
                        type=data.type,
                        project=data.project,
                        url=data.url,
                    )
                ).validate()
            return data

    async def delete_registry(self, purger: ContainerRegistryPurger) -> ContainerRegistryData:
        """Delete a container registry with the graph it left; its project relations go
        with it through the foreign key. Raises ContainerRegistryNotFound if absent."""
        async with self._ops_provider.write_ops() as w:
            data = await w.purge_entity(purger)
            if data is None:
                raise ContainerRegistryNotFound(
                    f"Container registry not found (id:{purger.registry_id})"
                )
            return data

    @container_registry_repository_resilience.apply()
    async def get_by_registry_and_project(
        self,
        registry_name: str,
        project: str | None = None,
    ) -> ContainerRegistryData:
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await self._get_by_registry_and_project(session, registry_name, project)
            if not result:
                raise ContainerRegistryNotFound()
            return result

    @container_registry_repository_resilience.apply()
    async def get_by_registry_name(self, registry_name: str) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name
            )
            result = await session.execute(stmt)
            rows = list(result.scalars().all())
            return [row.to_dataclass() for row in rows]

    @container_registry_repository_resilience.apply()
    async def get_all(self) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow)
            result = await session.execute(stmt)
            rows = list(result.scalars().all())
            return [row.to_dataclass() for row in rows]

    @container_registry_repository_resilience.apply()
    async def clear_images(
        self,
        registry_name: str,
        project: str | None = None,
    ) -> ContainerRegistryData:
        async with self._db.begin_session() as session:
            # Clear images
            update_stmt = (
                sa.update(ImageRow)
                .where(ImageRow.registry == registry_name)
                .where(ImageRow.status != ImageStatus.DELETED)
                .values(status=ImageStatus.DELETED)
            )
            if project:
                update_stmt = update_stmt.where(ImageRow.project == project)

            await session.execute(update_stmt)

            # Return registry data
            result = await self._get_by_registry_and_project(session, registry_name, project)
            if not result:
                raise ContainerRegistryNotFound()
            return result

    @container_registry_repository_resilience.apply()
    async def get_known_registries(self) -> dict[str, str]:
        async with self._db.begin_readonly_session_read_committed() as session:
            known_registries_map = await ContainerRegistryRow.get_known_container_registries(
                session
            )

            known_registries = {}
            for project, registries in known_registries_map.items():
                for registry_name, url in registries.items():
                    if project not in known_registries:
                        known_registries[f"{project}/{registry_name}"] = url.human_repr()

            return known_registries

    @container_registry_repository_resilience.apply()
    async def get_registry_by_url_and_project(
        self,
        registry_url: str,
        project: str,
    ) -> ContainerRegistryRow | None:
        """Find a Harbor2 registry row matching the given URL and project."""
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                (ContainerRegistryRow.type == ContainerRegistryType.HARBOR2)
                & (ContainerRegistryRow.url.like(f"%{registry_url}%"))
                & (ContainerRegistryRow.project == project)
            )
            result = await session.execute(stmt)
            return result.scalars().one_or_none()

    @container_registry_repository_resilience.apply()
    async def get_registry_row_for_scanner(
        self,
        registry_name: str,
        project: str | None = None,
    ) -> ContainerRegistryRow:
        """
        Get the raw ContainerRegistryRow object needed for container registry scanner.
        Raises ContainerRegistryNotFound if registry is not found.
        TODO: Refactor to return ContainerRegistryData when Registry Scanner is updated
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: ContainerRegistryRow | None = await session.scalar(stmt)
            if not row:
                raise ContainerRegistryNotFound()
            return row

    @container_registry_repository_resilience.apply()
    async def search_container_registries(
        self,
        querier: BatchQuerier,
    ) -> ContainerRegistrySearchResult:
        """Search container registries with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            ContainerRegistrySearchResult with items, total_count, and pagination info.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ContainerRegistryRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            return ContainerRegistrySearchResult(
                items=[row.ContainerRegistryRow.to_dataclass() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def _handle_allowed_groups_update(
        self,
        ops: V2RelationWriteOps,
        registry_id: ContainerRegistryID,
        allowed_group_updates: AllowedGroupsModel,
    ) -> None:
        """Relate the registry to the projects to add and unrelate it from the ones to
        remove. Raises ContainerRegistryGroupsAlreadyAssociated on a project already
        related and ContainerRegistryGroupsAssociationNotFound when none to remove was.
        """
        for raw_project_id in allowed_group_updates.add:
            project_id = ProjectID(uuid.UUID(raw_project_id))
            await ops.create_relation(ContainerRegistryProjectCreator(), project_id, registry_id)

        if allowed_group_updates.remove:
            unlinked = 0
            for raw_project_id in allowed_group_updates.remove:
                project_id = ProjectID(uuid.UUID(raw_project_id))
                if await ops.purge_relation(
                    ContainerRegistryProjectPurger(), project_id, registry_id
                ):
                    unlinked += 1
            if unlinked == 0:
                raise ContainerRegistryGroupsAssociationNotFound(
                    f"Tried to remove non-existing associations for registry_id: {registry_id}, group_ids: {allowed_group_updates.remove}"
                )

    async def _get_by_registry_and_project(
        self,
        session: SASession,
        registry_name: str,
        project: str | None = None,
    ) -> ContainerRegistryData | None:
        stmt = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == registry_name,
        )
        if project:
            stmt = stmt.where(ContainerRegistryRow.project == project)

        row: ContainerRegistryRow | None = await session.scalar(stmt)
        return row.to_dataclass() if row else None
