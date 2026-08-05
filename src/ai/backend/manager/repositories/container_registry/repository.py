import logging
import uuid
from typing import cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.data.entity.container_registry import (
    CONTAINER_REGISTRY_ENTITY_TYPE,
    CONTAINER_REGISTRY_SCOPE_TYPE,
)
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.types import EntityRef, ScopeRef
from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.container_registry import ContainerRegistryID
from ai.backend.common.identifier.project import ProjectID
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
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.pagination import NoPagination
from ai.backend.manager.repositories.base.purger import BatchPurger, Purger
from ai.backend.manager.repositories.base.querier import (
    BatchQuerier,
    Querier,
    execute_batch_querier,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.container_registry.creators import (
    ContainerRegistryCreatorSpec,
    ContainerRegistryGroupCreatorSpec,
    ContainerRegistryScopeCreation,
)
from ai.backend.manager.repositories.container_registry.purgers import (
    ContainerRegistryGroupPurgerSpec,
    ContainerRegistryPurgerSpec,
)
from ai.backend.manager.repositories.container_registry.updaters import (
    ContainerRegistryUpdaterSpec,
)
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    RBACOpsProvider,
    RBACWriteOps,
    ScopeDeletion,
    ScopeEntityMember,
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
    _rbac_ops_provider: RBACOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._rbac_ops_provider = RBACOpsProvider(db)

    async def create_registry(
        self,
        creator: Creator[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        """Create a container registry with its owner virtual scope.

        The registry becomes a scope of its own so the entities it owns (images)
        resolve through the virtual-scope chain; allowed projects are bound to
        that virtual scope to reach them.
        """
        spec = cast(ContainerRegistryCreatorSpec, creator.spec)
        async with self._rbac_ops_provider.write_ops() as w:
            creation_result = await w.create_scope(ContainerRegistryScopeCreation(spec=spec))
            container_registry_row = creation_result.row

            if spec.has_allowed_groups:
                allowed_groups = cast(AllowedGroupsModel, spec.allowed_groups)
                await self._handle_allowed_groups_update(
                    w, ContainerRegistryID(container_registry_row.id), allowed_groups
                )

            return container_registry_row.to_dataclass()

    async def modify_registry(
        self,
        updater: Updater[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        updater.spec = cast(ContainerRegistryUpdaterSpec, updater.spec)
        registry_id = ContainerRegistryID(cast(uuid.UUID, updater.pk_value))
        async with self._rbac_ops_provider.write_ops() as w:
            existing = await w.query(Querier(row_class=ContainerRegistryRow, pk_value=registry_id))
            if existing is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")

            is_global_value = updater.spec.is_global.optional_value()
            if is_global_value is True:
                await self._clear_all_allowed_groups(w, registry_id)
            elif updater.spec.has_allowed_groups_update is True:
                await self._handle_allowed_groups_update(
                    w, registry_id, updater.spec.allowed_groups.value()
                )

            to_update = updater.spec.build_values()
            if to_update == {}:  # means no fields to update or only allowed_groups updated
                return existing.row.to_dataclass()

            update_result = await w.update(updater)
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
        Delete a container registry with its RBAC entries and virtual scope.
        Returns the deleted registry data.
        Raises ContainerRegistryNotFound if registry doesn't exist.
        """
        spec = cast(ContainerRegistryPurgerSpec, purger.spec)
        async with self._rbac_ops_provider.write_ops() as w:
            await self._clear_all_allowed_groups(w, spec.registry_id)
            result = await w.delete_scope(
                ScopeDeletion(
                    purger=RBACEntityPurger(spec=spec),
                    scope=ScopeRef(
                        scope_type=CONTAINER_REGISTRY_SCOPE_TYPE, scope_id=spec.registry_id
                    ),
                )
            )
            if result is None:
                raise ContainerRegistryNotFound(
                    f"Container registry not found (id:{purger.spec.pk_value()})"
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
        ops: RBACWriteOps,
        registry_id: ContainerRegistryID,
        allowed_group_updates: AllowedGroupsModel,
    ) -> None:
        """
        Handle adding/removing group associations for a container registry.

        Each allowed project enrolls the registry as an entity member (virtual-scope
        membership + scope-entity association) and is bound to the registry's virtual
        scope so project-scoped permissions reach the registry's entities.

        Args:
            ops: RBAC write ops bound to the current transaction
            registry_id: Container registry UUID
            allowed_group_updates: Groups to add or remove

        Raises:
            ContainerRegistryGroupsAlreadyAssociated: If groups are already associated
            ContainerRegistryGroupsAssociationNotFound: If trying to remove non-existing associations
        """
        registry_scope = ScopeRef(scope_type=CONTAINER_REGISTRY_SCOPE_TYPE, scope_id=registry_id)
        # Registries created before the virtual-scope rollout have no virtual scope node.
        await ops.ensure_scope(registry_scope)

        for raw_project_id in allowed_group_updates.add:
            project_id = ProjectID(uuid.UUID(raw_project_id))
            await ops.create(
                Creator(
                    spec=ContainerRegistryGroupCreatorSpec(
                        registry_id=registry_id,
                        project_id=project_id,
                    )
                )
            )
            await self._enroll_registry_in_project(ops, registry_id, project_id)

        if allowed_group_updates.remove:
            total_deleted = 0
            for raw_project_id in allowed_group_updates.remove:
                project_id = ProjectID(uuid.UUID(raw_project_id))
                total_deleted += await self._withdraw_registry_from_project(
                    ops, registry_id, project_id
                )
            if total_deleted == 0:
                raise ContainerRegistryGroupsAssociationNotFound(
                    f"Tried to remove non-existing associations for registry_id: {registry_id}, group_ids: {allowed_group_updates.remove}"
                )

    async def _clear_all_allowed_groups(
        self,
        ops: RBACWriteOps,
        registry_id: ContainerRegistryID,
    ) -> None:
        registry_scope = ScopeRef(scope_type=CONTAINER_REGISTRY_SCOPE_TYPE, scope_id=registry_id)
        await ops.ensure_scope(registry_scope)
        result = await ops.batch_query_in_global(
            sa.select(AssociationContainerRegistriesGroupsRow.group_id).where(
                AssociationContainerRegistriesGroupsRow.registry_id == registry_id
            ),
            BatchQuerier(pagination=NoPagination()),
        )
        for row in result.rows:
            await self._withdraw_registry_from_project(ops, registry_id, ProjectID(row.group_id))

    async def _enroll_registry_in_project(
        self,
        ops: RBACWriteOps,
        registry_id: ContainerRegistryID,
        project_id: ProjectID,
    ) -> None:
        """Enroll the registry in the project's virtual scope and let the project
        scope reach the registry's own entities."""
        registry_scope = ScopeRef(scope_type=CONTAINER_REGISTRY_SCOPE_TYPE, scope_id=registry_id)
        project_scope = ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id)
        await ops.ensure_scope(project_scope)
        await ops.add_entity_members(
            EntityMembersAddition(
                scope=project_scope,
                members=[
                    ScopeEntityMember(
                        ref=EntityRef(
                            entity_type=CONTAINER_REGISTRY_ENTITY_TYPE,
                            entity_id=registry_id,
                        )
                    )
                ],
            )
        )
        await ops.bind_scope(project_scope, registry_scope, permission_cap=None)

    async def _withdraw_registry_from_project(
        self,
        ops: RBACWriteOps,
        registry_id: ContainerRegistryID,
        project_id: ProjectID,
    ) -> int:
        """Reverse :meth:`_enroll_registry_in_project` and delete the N:N mapping row.

        Returns the number of deleted mapping rows.
        """
        registry_scope = ScopeRef(scope_type=CONTAINER_REGISTRY_SCOPE_TYPE, scope_id=registry_id)
        project_scope = ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id)
        purge_result = await ops.batch_purge(
            BatchPurger(
                spec=ContainerRegistryGroupPurgerSpec(
                    registry_id=registry_id,
                    project_id=project_id,
                )
            )
        )
        await ops.remove_entity_members(
            project_scope,
            [EntityRef(entity_type=CONTAINER_REGISTRY_ENTITY_TYPE, entity_id=registry_id)],
        )
        await ops.unbind_scope(project_scope, registry_scope)
        return purge_result.deleted_count

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
