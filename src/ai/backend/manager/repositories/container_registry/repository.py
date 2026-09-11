import logging
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryData,
)
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.container_registry.creators import ContainerRegistryCreator
from ai.backend.manager.models.container_registry.purgers import ContainerRegistryPurger
from ai.backend.manager.models.container_registry.searchable_fields import (
    ContainerRegistrySearchableFields,
)
from ai.backend.manager.models.container_registry.updaters import (
    ContainerRegistryGlobalUpdater,
    ContainerRegistryUpdater,
)
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# How many images join or leave `public` per transaction when a registry is switched.
IMAGE_MEMBERSHIP_CHUNK_SIZE = 1000

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
    _ops_provider: ShareOpsProvider
    _db_source: ContainerRegistryDBSource

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: ShareOpsProvider) -> None:
        self._db = db
        self._ops_provider = ops_provider
        self._db_source = ContainerRegistryDBSource(ops_provider)

    async def create_registry(
        self,
        creator: ContainerRegistryCreator,
    ) -> ContainerRegistryData:
        """Create a container registry with its own virtual entity, in the scopes the
        creator names."""
        async with self._ops_provider.write_ops() as w:
            return await w.create_entity(creator)

    async def modify_registry(
        self,
        updater: ContainerRegistryUpdater,
    ) -> ContainerRegistryData:
        registry_id = updater.registry_id
        async with self._ops_provider.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")
            return data

    async def set_global(self, updater: ContainerRegistryGlobalUpdater) -> ContainerRegistryData:
        """Write `is_global` and put the registry and its images into the `public`
        scope, or take them out.

        The registry goes in before its images and comes out after them, so a run that
        stops part way leaves `public` holding no image of a registry it cannot reach.
        Every step is idempotent: repeating the same call finishes what was left.
        """
        if not updater.is_global:
            await self._move_images(updater.registry_id, to_public=False)
            return await self._write_global(updater)
        data = await self._write_global(updater)
        await self._move_images(updater.registry_id, to_public=True)
        return data

    async def _write_global(self, updater: ContainerRegistryGlobalUpdater) -> ContainerRegistryData:
        """Write `is_global` and settle the registry's own membership of `public`, in
        one transaction."""
        public = global_entity_id(GlobalEntityName.PUBLIC)
        async with self._ops_provider.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise ContainerRegistryNotFound(
                    f"Container registry not found (id:{updater.registry_id})"
                )
            if updater.is_global:
                await w.add_membership([public], [updater.registry_id])
            else:
                await w.remove_membership([public], [updater.registry_id])
            return data

    async def _move_images(self, registry_id: ContainerRegistryID, *, to_public: bool) -> None:
        """Every image of the registry joins `public` or leaves it, a chunk per
        transaction so the row count does not bound the statement."""
        public = global_entity_id(GlobalEntityName.PUBLIC)
        after: uuid.UUID | None = None
        while True:
            async with self._db.begin_readonly_session() as sess:
                stmt = (
                    sa.select(ImageRow.id)
                    .where(ImageRow.registry_id == registry_id)
                    .order_by(ImageRow.id)
                    .limit(IMAGE_MEMBERSHIP_CHUNK_SIZE)
                )
                if after is not None:
                    stmt = stmt.where(ImageRow.id > after)
                image_ids = [ImageID(row) for row in (await sess.scalars(stmt)).all()]
            if not image_ids:
                return
            async with self._ops_provider.write_ops() as w:
                if to_public:
                    await w.add_membership([public], image_ids)
                else:
                    await w.remove_membership([public], image_ids)
            after = image_ids[-1]

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
            return [ContainerRegistrySearchableFields.own.to_data(row) for row in rows]

    @container_registry_repository_resilience.apply()
    async def get_all(self) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow)
            result = await session.execute(stmt)
            rows = list(result.scalars().all())
            return [ContainerRegistrySearchableFields.own.to_data(row) for row in rows]

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
    async def get_project_registry(self, scope_id: ProjectScope) -> ContainerRegistryData:
        registry_id = await self._db_source.lookup_image_commit_registry_id(
            ProjectID(scope_id.project_id)
        )
        return await self._db_source.fetch_by_id(registry_id)

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
        return ContainerRegistrySearchableFields.own.to_data(row) if row else None
