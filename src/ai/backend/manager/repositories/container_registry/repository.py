import logging
import uuid
from collections.abc import Collection
from dataclasses import dataclass
from typing import cast, override

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.data.entity.types import EntityRef, ScopeRef
from ai.backend.common.data.entity.types import EntityType as VirtualScopeEntityType
from ai.backend.common.data.entity.types import ScopeType as VirtualScopeType
from ai.backend.common.data.permission.types import RBACElementType
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
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.container_registry.creators import (
    ContainerRegistryCreatorSpec,
    ContainerRegistryGroupCreatorSpec,
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
    ScopeCreation,
    ScopeDeletion,
    ScopeEntityMember,
)
from ai.backend.manager.repositories.permission_controller.role_manager import (
    ScopeSystemRoleData,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_CONTAINER_REGISTRY_SCOPE_TYPE = VirtualScopeType(RBACElementType.CONTAINER_REGISTRY.value)
_CONTAINER_REGISTRY_ENTITY_TYPE = VirtualScopeEntityType(RBACElementType.CONTAINER_REGISTRY.value)
_PROJECT_SCOPE_TYPE = VirtualScopeType(RBACElementType.PROJECT.value)


def _registry_scope(registry_id: uuid.UUID) -> ScopeRef:
    return ScopeRef(scope_type=_CONTAINER_REGISTRY_SCOPE_TYPE, scope_id=registry_id)


def _registry_entity(registry_id: uuid.UUID) -> EntityRef:
    return EntityRef(entity_type=_CONTAINER_REGISTRY_ENTITY_TYPE, entity_id=registry_id)


def _project_scope(group_id: uuid.UUID) -> ScopeRef:
    return ScopeRef(scope_type=_PROJECT_SCOPE_TYPE, scope_id=group_id)


@dataclass
class ContainerRegistryScopeCreation(ScopeCreation[ContainerRegistryRow]):
    """Creates a container registry row and the scope the registry becomes.

    A registry has no owning scope of its own (``scope_ref=None``); projects
    reach it and its images through allowed-group bindings instead.
    """

    spec: ContainerRegistryCreatorSpec

    @override
    def creator(self) -> RBACEntityCreator[ContainerRegistryRow]:
        return RBACEntityCreator(
            spec=self.spec,
            element_type=RBACElementType.CONTAINER_REGISTRY,
            scope_ref=None,
        )

    @override
    def scope_of(self, row: ContainerRegistryRow) -> ScopeRef:
        return _registry_scope(row.id)

    @override
    def system_roles_of(self, row: ContainerRegistryRow) -> Collection[ScopeSystemRoleData]:
        return ()


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
        """Create a registry with its virtual scope, so it can own the images
        scanned from it; allowed groups are bound into that scope."""
        spec = cast(ContainerRegistryCreatorSpec, creator.spec)
        async with self._rbac_ops_provider.write_ops() as w:
            creation_result = await w.create_scope(ContainerRegistryScopeCreation(spec=spec))
            container_registry_row = creation_result.row

            if spec.has_allowed_groups:
                allowed_groups = cast(AllowedGroupsModel, spec.allowed_groups)
                await self._handle_allowed_groups_update(
                    w, container_registry_row.id, allowed_groups
                )

            return container_registry_row.to_dataclass()

    async def modify_registry(
        self,
        updater: Updater[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        async with self._rbac_ops_provider.write_ops() as w:
            updater.spec = cast(ContainerRegistryUpdaterSpec, updater.spec)
            registry_id = cast(uuid.UUID, updater.pk_value)

            existing = await w.query(Querier(row_class=ContainerRegistryRow, pk_value=registry_id))
            if existing is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")
            reg_row = existing.row

            is_global_value = updater.spec.is_global.optional_value()
            if is_global_value is True:
                await self._clear_all_allowed_groups(w, registry_id)
            elif updater.spec.has_allowed_groups_update is True:
                await self._handle_allowed_groups_update(
                    w, registry_id, updater.spec.allowed_groups.value()
                )

            to_update = updater.spec.build_values()
            if to_update == {}:  # means no fields to update or only allowed_groups updated
                return reg_row.to_dataclass()

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
            result = await w.delete_scope(
                ScopeDeletion(
                    purger=RBACEntityPurger(spec=spec),
                    scope=_registry_scope(spec.registry_id),
                )
            )

            if result is None:
                raise ContainerRegistryNotFound(
                    f"Container registry not found (id:{spec.registry_id})"
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
        w: RBACWriteOps,
        registry_id: uuid.UUID,
        allowed_group_updates: AllowedGroupsModel,
    ) -> None:
        """
        Handle adding/removing group associations for a container registry.

        An allowed group is expressed on the virtual-scope chain in both
        directions: the registry becomes an entity member of the project's
        virtual scope (the project sees the registry itself), and the project
        scope is bound into the registry's virtual scope (project-scoped
        permissions reach the registry's images).

        Args:
            w: RBAC write ops bound to the current transaction
            registry_id: Container registry UUID
            allowed_group_updates: Groups to add or remove

        Raises:
            ContainerRegistryGroupsAlreadyAssociated: If groups are already associated
            ContainerRegistryGroupsAssociationNotFound: If trying to remove non-existing associations
        """
        registry_scope = _registry_scope(registry_id)

        if allowed_group_updates.add:
            # Registries created before the virtual-scope chain have no node yet.
            await w.ensure_scope(registry_scope)
            for raw_group_id in allowed_group_updates.add:
                group_id = uuid.UUID(raw_group_id)
                await w.create(
                    Creator(
                        spec=ContainerRegistryGroupCreatorSpec(
                            registry_id=registry_id,
                            group_id=group_id,
                        )
                    )
                )
                project_scope = _project_scope(group_id)
                await w.add_entity_members(
                    EntityMembersAddition(
                        scope=project_scope,
                        members=[ScopeEntityMember(ref=_registry_entity(registry_id))],
                    )
                )
                await w.bind_scope(project_scope, registry_scope, permission_cap=None)

        if allowed_group_updates.remove:
            await w.ensure_scope(registry_scope)
            total_deleted = 0
            for raw_group_id in allowed_group_updates.remove:
                group_id = uuid.UUID(raw_group_id)
                total_deleted += await self._remove_allowed_group(w, registry_id, group_id)
            if total_deleted == 0:
                raise ContainerRegistryGroupsAssociationNotFound(
                    f"Tried to remove non-existing associations for registry_id: {registry_id}, group_ids: {allowed_group_updates.remove}"
                )

    async def _clear_all_allowed_groups(
        self,
        w: RBACWriteOps,
        registry_id: uuid.UUID,
    ) -> None:
        stmt = sa.select(AssociationContainerRegistriesGroupsRow.group_id).where(
            AssociationContainerRegistriesGroupsRow.registry_id == registry_id
        )
        result = await w.batch_query_in_global(stmt, BatchQuerier(pagination=NoPagination()))
        group_ids = [row.group_id for row in result.rows]
        if not group_ids:
            return
        await w.ensure_scope(_registry_scope(registry_id))
        for group_id in group_ids:
            await self._remove_allowed_group(w, registry_id, group_id)

    async def _remove_allowed_group(
        self,
        w: RBACWriteOps,
        registry_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> int:
        """Drop an allowed-group association: the N:N mapping row and both
        virtual-scope edges. Returns the number of mapping rows deleted."""
        purge_result = await w.batch_purge(
            BatchPurger(
                spec=ContainerRegistryGroupPurgerSpec(
                    registry_id=registry_id,
                    group_id=group_id,
                )
            )
        )
        project_scope = _project_scope(group_id)
        await w.remove_entity_members(project_scope, [_registry_entity(registry_id)])
        await w.unbind_scope(project_scope, _registry_scope(registry_id))
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
