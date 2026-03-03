import logging
import uuid
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.image import (
    ContainerRegistryGroupsAssociationNotFound,
    ContainerRegistryNotFound,
)
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    Creator,
    execute_bulk_creator,
    execute_creator,
)
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.container_registry.creators import (
    ContainerRegistryCreatorSpec,
    ContainerRegistryGroupCreatorSpec,
)
from ai.backend.manager.repositories.container_registry.updaters import (
    ContainerRegistryUpdaterSpec,
)

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

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create_registry(
        self,
        creator: Creator[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        spec = cast(ContainerRegistryCreatorSpec, creator.spec)
        async with self._db.begin_session() as session:
            creator_result = await execute_creator(session, creator)
            container_registry_row: ContainerRegistryRow = creator_result.row

            if spec.has_allowed_groups:
                allowed_groups = cast(AllowedGroupsModel, spec.allowed_groups)
                await self._handle_allowed_groups_update(
                    session, container_registry_row.id, allowed_groups
                )

            return container_registry_row.to_dataclass()

    async def modify_registry(
        self,
        updater: Updater[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        async with self._db.begin_session() as session:
            updater.spec = cast(ContainerRegistryUpdaterSpec, updater.spec)
            registry_id = cast(uuid.UUID, updater.pk_value)

            stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
            result = await session.execute(stmt)
            reg_row = result.scalar_one_or_none()

            if reg_row is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")

            is_global_value = updater.spec.is_global.optional_value()
            if is_global_value is True:
                await self._clear_all_allowed_groups(session, registry_id)
            elif updater.spec.has_allowed_groups_update is True:
                await self._handle_allowed_groups_update(
                    session, registry_id, updater.spec.allowed_groups.value()
                )

            to_update = updater.spec.build_values()
            if to_update == {}:  # means no fields to update or only allowed_groups updated
                return reg_row.to_dataclass()

            session.expire(reg_row)  # Expire to get updated values after update
            update_result = await execute_updater(session, updater)
            if update_result is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")

            reg_row = update_result.row
            validator = ContainerRegistryValidator(
                ContainerRegistryValidatorArgs(
                    type=reg_row.type,
                    project=reg_row.project,
                    url=reg_row.url,
                )
            )
            validator.validate()
            return reg_row.to_dataclass()

    async def delete_registry(self, purger: Purger[ContainerRegistryRow]) -> ContainerRegistryData:
        """
        Delete a container registry using a purger.
        Returns the deleted registry data.
        Raises ContainerRegistryNotFound if registry doesn't exist.
        """
        async with self._db.begin_session() as session:
            result = await execute_purger(session, purger)

            if result is None:
                raise ContainerRegistryNotFound(
                    f"Container registry not found (id:{purger.pk_value})"
                )

            return result.row.to_dataclass()

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
        session: SASession,
        registry_id: uuid.UUID,
        allowed_group_updates: AllowedGroupsModel,
    ) -> None:
        """
        Handle adding/removing group associations for a container registry.

        Args:
            session: Database session
            registry_id: Container registry UUID
            allowed_group_updates: Groups to add or remove

        Raises:
            ContainerRegistryGroupsAlreadyAssociated: If groups are already associated
            ContainerRegistryGroupsAssociationNotFound: If trying to remove non-existing associations
        """
        if allowed_group_updates.add:
            specs = [
                ContainerRegistryGroupCreatorSpec(
                    registry_id=registry_id,
                    group_id=uuid.UUID(group_id),
                )
                for group_id in allowed_group_updates.add
            ]
            bulk_creator = BulkCreator(specs=specs)
            await execute_bulk_creator(session, bulk_creator)

        if allowed_group_updates.remove:
            delete_query = (
                sa.delete(AssociationContainerRegistriesGroupsRow)
                .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
                .where(
                    AssociationContainerRegistriesGroupsRow.group_id.in_(
                        allowed_group_updates.remove
                    )
                )
            )
            result = await session.execute(delete_query)
            if cast(CursorResult[Any], result).rowcount == 0:
                raise ContainerRegistryGroupsAssociationNotFound(
                    f"Tried to remove non-existing associations for registry_id: {registry_id}, group_ids: {allowed_group_updates.remove}"
                )

    async def _clear_all_allowed_groups(
        self,
        session: SASession,
        registry_id: uuid.UUID,
    ) -> None:
        delete_query = sa.delete(AssociationContainerRegistriesGroupsRow).where(
            AssociationContainerRegistriesGroupsRow.registry_id == registry_id
        )
        await session.execute(delete_query)

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
