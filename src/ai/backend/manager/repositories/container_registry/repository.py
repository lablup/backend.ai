import logging
import uuid
from typing import Optional, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.common.exception import BackendAIError, ContainerRegistryGroupsAlreadyAssociated
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
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
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

            if updater.spec.has_allowed_groups_update is True:
                await self._update_registry_access_allowed_groups(
                    session,
                    registry_id,
                    updater.spec.allowed_groups.value(),
                )

            to_update = updater.spec.build_values()
            if to_update == {}:  # means no fields to update or only allowed_groups updated
                return reg_row.to_dataclass()

            session.expire(reg_row)  # Expire to get updated values after update
            result = await execute_updater(session, updater)
            if result is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")

            reg_row = result.row
            validator = ContainerRegistryValidator(
                ContainerRegistryValidatorArgs(
                    type=reg_row.type,
                    project=reg_row.project,
                    url=reg_row.url,
                )
            )
            validator.validate()
            return reg_row.to_dataclass()

    async def _update_registry_access_allowed_groups(
        self, session: SASession, registry_id: uuid.UUID, allowed_groups: AllowedGroupsModel
    ) -> None:
        if allowed_groups.add:
            existing_stmt = sa.select(AssociationContainerRegistriesGroupsRow.group_id).where(
                AssociationContainerRegistriesGroupsRow.registry_id == registry_id
            )
            result = await session.execute(existing_stmt)
            # Convert UUID objects to strings for comparison with allowed_groups.add
            existing_group_ids = {str(gid) for gid in result.scalars().all()}

            # Check if any group is already associated
            already_associated = [gid for gid in allowed_groups.add if gid in existing_group_ids]
            if already_associated:
                raise ContainerRegistryGroupsAlreadyAssociated(
                    f"Groups are already associated with registry_id: {registry_id}, group_ids: {already_associated}"
                )

            # Add new group associations
            insert_values = [
                {"registry_id": registry_id, "group_id": group_id}
                for group_id in allowed_groups.add
            ]
            insert_query = sa.insert(AssociationContainerRegistriesGroupsRow).values(insert_values)
            await session.execute(insert_query)
        if allowed_groups.remove:
            delete_query = (
                sa.delete(AssociationContainerRegistriesGroupsRow)
                .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
                .where(AssociationContainerRegistriesGroupsRow.group_id.in_(allowed_groups.remove))
            )
            result = await session.execute(delete_query)
            if result.rowcount == 0:
                raise ContainerRegistryGroupsAssociationNotFound(
                    f"Tried to remove non-existing associations for registry_id: {registry_id}, group_ids: {allowed_groups.remove}"
                )

    @container_registry_repository_resilience.apply()
    async def get_by_registry_and_project(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        async with self._db.begin_readonly_session() as session:
            result = await self._get_by_registry_and_project(session, registry_name, project)
            if not result:
                raise ContainerRegistryNotFound()
            return result

    @container_registry_repository_resilience.apply()
    async def get_by_registry_name(self, registry_name: str) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name
            )
            result = await session.execute(stmt)
            rows: list[ContainerRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @container_registry_repository_resilience.apply()
    async def get_all(self) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow)
            result = await session.execute(stmt)
            rows: list[ContainerRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @container_registry_repository_resilience.apply()
    async def clear_images(
        self,
        registry_name: str,
        project: Optional[str] = None,
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
        async with self._db.begin_readonly_session() as session:
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
        project: Optional[str] = None,
    ) -> ContainerRegistryRow:
        """
        Get the raw ContainerRegistryRow object needed for container registry scanner.
        Raises ContainerRegistryNotFound if registry is not found.
        TODO: Refactor to return ContainerRegistryData when Registry Scanner is updated
        """
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: Optional[ContainerRegistryRow] = await session.scalar(stmt)
            if not row:
                raise ContainerRegistryNotFound()
            return row

    async def _get_by_registry_and_project(
        self,
        session: SASession,
        registry_name: str,
        project: Optional[str] = None,
    ) -> Optional[ContainerRegistryData]:
        stmt = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == registry_name,
        )
        if project:
            stmt = stmt.where(ContainerRegistryRow.project == project)

        row: Optional[ContainerRegistryRow] = await session.scalar(stmt)
        return row.to_dataclass() if row else None
