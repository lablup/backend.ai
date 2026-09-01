"""Database source for resource group repository operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.resource_group import (
    RESOURCE_GROUP_ENTITY_TYPE,
    RESOURCE_GROUP_SCOPE_TYPE,
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.data.entity.types import EntityRef, EntityType, ScopeRef, ScopeType
from ai.backend.common.exception import DomainNotFound
from ai.backend.common.types import SlotQuantity
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.resource_group.types import (
    ResourceGroupData,
    ResourceGroupListResult,
    ResourceInfo,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
    query_allowed_sgroups,
)
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    BulkCreatorResultWithFailures,
    execute_bulk_creator,
)
from ai.backend.manager.repositories.base.purger import (
    BatchPurger,
    execute_batch_purger,
)
from ai.backend.manager.repositories.base.rbac.scope_binder import RBACScopeBinder
from ai.backend.manager.repositories.base.rbac.scope_unbinder import RBACScopeEntityUnbinder
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    RBACOpsProvider,
    RBACWriteOps,
    ScopeEntityMember,
)
from ai.backend.manager.repositories.resource_group.creators import (
    ResourceGroupForDomainCreatorSpec,
    ResourceGroupForProjectCreatorSpec,
)
from ai.backend.manager.repositories.resource_group.purgers import (
    DomainsForResourceGroupPurgerSpec,
    ProjectsForResourceGroupPurgerSpec,
    ResourceGroupsForDomainPurgerSpec,
    ResourceGroupsForProjectPurgerSpec,
)
from ai.backend.manager.repositories.resource_slot.types import subtract_quantities

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = (
    "ResourceGroupDBSource",
    "ResourceGroupListResult",
)


class ResourceGroupDBSource:
    """
    Database source for resource group operations.
    Handles all database operations for resource groups.
    """

    _db: ExtendedAsyncSAEngine
    _rbac_ops_provider: RBACOpsProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db
        self._rbac_ops_provider = RBACOpsProvider(db)

    def _resource_group_scope(self, resource_group_id: ResourceGroupID) -> ScopeRef:
        return ScopeRef(scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=resource_group_id)

    def _resource_group_entity(self, resource_group_id: ResourceGroupID) -> EntityRef:
        return EntityRef(entity_type=RESOURCE_GROUP_ENTITY_TYPE, entity_id=resource_group_id)

    def _scope_ref_of(self, ref: RBACElementRef) -> ScopeRef:
        """Convert an RBAC element ref addressing a scope-capable element to a ScopeRef."""
        return ScopeRef(
            scope_type=ScopeType(EntityType(ref.element_type.value)),
            scope_id=uuid.UUID(ref.element_id),
        )

    def _tolerate_only_duplicates[TRow: Base](
        self, result: BulkCreatorResultWithFailures[TRow]
    ) -> None:
        """Re-raise partial-create failures that are not duplicate-row conflicts; an already
        existing mapping row is fine (the add operations are idempotent)."""
        for error in result.errors:
            if not isinstance(error.exception, UniqueConstraintViolationError):
                raise error.exception

    async def _get_domain_id(self, w: RBACWriteOps, domain_name: str) -> DomainID:
        result = await w.batch_query_in_global(
            sa.select(DomainRow.id).where(DomainRow.name == domain_name),
            BatchQuerier(pagination=NoPagination()),
        )
        if not result.rows:
            raise DomainNotFound(f"Domain '{domain_name}' not found")
        return DomainID(result.rows[0].id)

    async def _get_domain_ids_by_names(
        self,
        w: RBACWriteOps,
        domain_names: list[str],
    ) -> dict[str, DomainID]:
        if not domain_names:
            return {}
        result = await w.batch_query_in_global(
            sa.select(DomainRow.name, DomainRow.id).where(DomainRow.name.in_(domain_names)),
            BatchQuerier(pagination=NoPagination()),
        )
        return {row.name: row.id for row in result.rows}

    async def search_resource_groups(
        self,
        querier: BatchQuerier,
    ) -> ResourceGroupListResult:
        """Searches resource groups with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ResourceGroupRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.ResourceGroupRow.to_dataclass() for row in result.rows]

            return ResourceGroupListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def get_resource_group_id_by_name(self, name: ResourceGroupName) -> ResourceGroupID:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ResourceGroupRow.id).where(ResourceGroupRow.name == name)
            resource_group_id = await db_sess.scalar(query)
            if resource_group_id is None:
                raise ResourceGroupNotFound(name)
            return resource_group_id

    async def get_resource_group_ids_by_names(
        self,
        names: list[ResourceGroupName],
    ) -> dict[ResourceGroupName, ResourceGroupID]:
        """Resolve resource group row IDs from names; missing names are absent."""
        if not names:
            return {}
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            rows = await db_sess.execute(
                sa.select(ResourceGroupRow.name, ResourceGroupRow.id).where(
                    ResourceGroupRow.name.in_(names)
                )
            )
            return {ResourceGroupName(row.name): row.id for row in rows}

    async def get_resource_group_by_name(
        self,
        name: str,
    ) -> ResourceGroupData:
        """Get a single resource group by name (primary key).

        Args:
            name: The name of the resource group (primary key).

        Returns:
            ResourceGroupData for the requested resource group.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.get(ResourceGroupRow, name)
            if row is None:
                raise ResourceGroupNotFound(name)
            return row.to_dataclass()

    async def replace_default_deployment_options(
        self,
        name: ResourceGroupName,
        options: DeploymentOptions,
    ) -> DeploymentOptions:
        """Fully replace the ``default_deployment_options`` JSONB column
        and return the stored value in a single ``UPDATE ... RETURNING``
        round-trip.

        The column is typed as ``PydanticColumn(DeploymentOptions)`` so
        the domain model is persisted verbatim.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        async with self._db.begin_session() as session:
            stmt = (
                sa.update(ResourceGroupRow)
                .where(ResourceGroupRow.name == name)
                .values(default_deployment_options=options)
                .returning(ResourceGroupRow.default_deployment_options)
            )
            result = await session.execute(stmt)
            row = result.first()
            if row is None:
                raise ResourceGroupNotFound(f"Resource group not found (name:{name})")
            stored: DeploymentOptions = row[0]
            return stored

    async def replace_default_session_options(
        self,
        name: ResourceGroupName,
        options: DefaultSessionOptions,
    ) -> DefaultSessionOptions:
        """Fully replace the ``default_session_options`` JSONB column
        and return the stored value in a single ``UPDATE ... RETURNING``
        round-trip.

        The column is typed as ``PydanticColumn(DefaultSessionOptions)``
        so the domain model is persisted verbatim.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        async with self._db.begin_session() as session:
            stmt = (
                sa.update(ResourceGroupRow)
                .where(ResourceGroupRow.name == name)
                .values(default_session_options=options)
                .returning(ResourceGroupRow.default_session_options)
            )
            result = await session.execute(stmt)
            row = result.first()
            if row is None:
                raise ResourceGroupNotFound(f"Resource group not found (name:{name})")
            stored: DefaultSessionOptions = row[0]
            return stored

    async def associate_resource_group_with_domains(
        self,
        binder: RBACScopeBinder[ResourceGroupForDomainRow],
    ) -> None:
        """Associates a resource group with multiple domains, binding each domain scope
        to the resource group's virtual entity."""
        await self._associate_resource_groups(binder)

    async def disassociate_resource_group_with_domains(
        self,
        unbinder: RBACScopeEntityUnbinder[ResourceGroupForDomainRow],
    ) -> None:
        """Disassociates resource groups from a domain, unbinding the domain scope from
        each resource group's virtual entity."""
        await self._disassociate_resource_groups(unbinder)

    async def _associate_resource_groups[TRow: Base](self, binder: RBACScopeBinder[TRow]) -> None:
        """Create the N:N mapping rows and enroll each pair's resource group into the
        pair's scope (association row + membership), binding the scope to the resource
        group's virtual entity so it reaches the resource group's entities."""
        if not binder.pairs:
            return
        async with self._rbac_ops_provider.write_ops() as w:
            await w.bulk_create(BulkCreator(specs=[pair.spec for pair in binder.pairs]))
            for pair in binder.pairs:
                accessor_scope = self._scope_ref_of(pair.scope_ref)
                resource_group_id = ResourceGroupID(uuid.UUID(pair.entity_ref.element_id))
                await self._enroll_resource_groups(w, accessor_scope, [resource_group_id])

    async def _disassociate_resource_groups[TRow: Base](
        self, unbinder: RBACScopeEntityUnbinder[TRow]
    ) -> None:
        """Delete the N:N mapping rows and withdraw each resource group from the
        unbinder's scope (association row + membership + virtual-entity binding)."""
        async with self._rbac_ops_provider.write_ops() as w:
            accessor_scope = self._scope_ref_of(unbinder.scope_ref)
            entity_ids = unbinder.entity_ids
            if entity_ids is not None:
                resource_group_ids = [ResourceGroupID(uuid.UUID(eid)) for eid in entity_ids]
            else:
                result = await w.batch_query_in_global(
                    unbinder.build_purger_spec().build_subquery(),
                    BatchQuerier(pagination=NoPagination()),
                )
                resource_group_ids = [
                    ResourceGroupID(row[0].resource_group_id) for row in result.rows
                ]
            await w.batch_purge(BatchPurger(spec=unbinder.build_purger_spec()))
            await self._withdraw_resource_groups(w, accessor_scope, resource_group_ids)

    async def _enroll_resource_groups(
        self,
        w: RBACWriteOps,
        accessor_scope: ScopeRef,
        resource_group_ids: list[ResourceGroupID],
    ) -> None:
        """Enroll resource groups under ``accessor_scope`` as inheriting members:
        membership, the legacy scope association, and the scope's binding into each
        resource group's virtual entity. The virtual entities are ensured first, since
        rows created before the virtual-entity rollout may not have one."""
        if not resource_group_ids:
            return
        await w.ensure_scope(accessor_scope)
        for resource_group_id in resource_group_ids:
            await w.ensure_scope(self._resource_group_scope(resource_group_id))
        await w.add_bulk_inheriting_members(
            EntityMembersAddition(
                scope=accessor_scope,
                members=[
                    ScopeEntityMember(ref=self._resource_group_entity(resource_group_id))
                    for resource_group_id in resource_group_ids
                ],
            )
        )

    async def _withdraw_resource_groups(
        self,
        w: RBACWriteOps,
        accessor_scope: ScopeRef,
        resource_group_ids: list[ResourceGroupID],
    ) -> None:
        """Withdraw resource groups from ``accessor_scope`` via ``remove_bulk_members``:
        membership, the legacy scope association, and the scope's binding in each
        resource group's virtual entity (missing virtual entities never raise)."""
        if not resource_group_ids:
            return
        await w.remove_bulk_members(
            accessor_scope,
            [self._resource_group_entity(rg_id) for rg_id in resource_group_ids],
        )

    async def check_resource_group_domain_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        domain_id: DomainID,
    ) -> bool:
        """Checks if a resource group is associated with a domain."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(ResourceGroupForDomainRow)
                .where(
                    sa.and_(
                        ResourceGroupForDomainRow.resource_group_id == resource_group_id,
                        ResourceGroupForDomainRow.domain_id == domain_id,
                    )
                )
            )
            result = await session.scalar(query)
            return (result or 0) > 0

    async def associate_resource_group_with_keypairs(
        self,
        bulk_creator: BulkCreator[ResourceGroupForKeypairsRow],
    ) -> None:
        """Associates a resource group with multiple keypairs."""
        async with self._db.begin_session() as session:
            await execute_bulk_creator(session, bulk_creator)

    async def disassociate_resource_group_with_keypairs(
        self,
        purger: BatchPurger[ResourceGroupForKeypairsRow],
    ) -> None:
        """Disassociates a resource group from multiple keypairs."""
        async with self._db.begin_session() as session:
            await execute_batch_purger(session, purger)

    async def check_resource_group_keypair_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        access_key: str,
    ) -> bool:
        """Checks if a resource group is associated with a keypair."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(
                sa.exists().where(
                    sa.and_(
                        ResourceGroupForKeypairsRow.resource_group_id == resource_group_id,
                        ResourceGroupForKeypairsRow.access_key == access_key,
                    )
                )
            )
            result = await session.execute(query)
            return result.scalar() or False

    async def associate_resource_group_with_user_groups(
        self,
        binder: RBACScopeBinder[ResourceGroupForProjectRow],
    ) -> None:
        """Associates a resource group with multiple user groups (projects), binding each
        project scope to the resource group's virtual entity."""
        await self._associate_resource_groups(binder)

    async def disassociate_resource_group_with_user_groups(
        self,
        unbinder: RBACScopeEntityUnbinder[ResourceGroupForProjectRow],
    ) -> None:
        """Disassociates resource groups from a project, unbinding the project scope from
        each resource group's virtual entity."""
        await self._disassociate_resource_groups(unbinder)

    async def check_resource_group_user_group_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        user_group: uuid.UUID,
    ) -> bool:
        """Checks if a resource group is associated with a user group (project)."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(ResourceGroupForProjectRow)
                .where(
                    sa.and_(
                        ResourceGroupForProjectRow.resource_group_id == resource_group_id,
                        ResourceGroupForProjectRow.group == user_group,
                    )
                )
            )
            result = await session.scalar(query)
            return (result or 0) > 0

    async def list_allowed_sgroups(
        self,
        *,
        domain_name: str,
        group: str,
        access_key: str,
    ) -> list[ResourceGroupData]:
        """List allowed resource groups for a user using the legacy query_allowed_sgroups function.

        Returns ResourceGroupData for each allowed resource group.
        """
        async with self._db.begin_readonly() as conn:
            rows = await query_allowed_sgroups(conn, domain_name, group, access_key)
            # Convert raw rows to ResourceGroupData via ORM
            sg_names = [row.name for row in rows]

        if not sg_names:
            return []

        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(ResourceGroupRow)
                .where(ResourceGroupRow.name.in_(sg_names))
                .order_by(ResourceGroupRow.name)
            )
            result = await db_sess.execute(query)
            return [row.to_dataclass() for row in result.scalars()]

    async def get_resource_info(
        self,
        resource_group: str,
    ) -> ResourceInfo:
        """Get aggregated resource information for a resource group.

        Uses normalized agent_resources table with SQL-level aggregation.

        Args:
            scaling_group: The name of the resource group.

        Returns:
            ResourceInfo containing capacity, used, and free resource metrics.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        ar = AgentResourceRow.__table__
        ag = AgentRow.__table__
        rst = ResourceSlotTypeRow.__table__

        async with self._db.begin_readonly_session() as db_sess:
            # Validate resource group exists
            sg_exists = await db_sess.scalar(
                sa.select(sa.exists().where(ResourceGroupRow.name == resource_group))
            )
            if not sg_exists:
                raise ResourceGroupNotFound(resource_group)

            # Capacity: ALIVE + schedulable agents, JOIN rst for rank ordering
            capacity_stmt = (
                sa.select(ar.c.slot_name, sa.func.sum(ar.c.capacity).label("total"))
                .select_from(
                    ar.join(ag, ar.c.agent_id == ag.c.id).join(
                        rst, ar.c.slot_name == rst.c.slot_name
                    )
                )
                .where(
                    ag.c.scaling_group == resource_group,
                    ag.c.status == AgentStatus.ALIVE,
                    ag.c.schedulable == sa.true(),
                )
                .group_by(ar.c.slot_name, rst.c.rank)
                .order_by(rst.c.rank)
            )
            capacity_result = await db_sess.execute(capacity_stmt)
            capacity_list = [SlotQuantity(row.slot_name, row.total) for row in capacity_result]

            # Used: ALIVE agents (regardless of schedulable), JOIN rst for rank ordering
            used_stmt = (
                sa.select(ar.c.slot_name, sa.func.sum(ar.c.used).label("total"))
                .select_from(
                    ar.join(ag, ar.c.agent_id == ag.c.id).join(
                        rst, ar.c.slot_name == rst.c.slot_name
                    )
                )
                .where(
                    ag.c.scaling_group == resource_group,
                    ag.c.status == AgentStatus.ALIVE,
                )
                .group_by(ar.c.slot_name, rst.c.rank)
                .order_by(rst.c.rank)
            )
            used_result = await db_sess.execute(used_stmt)
            used_list = [SlotQuantity(row.slot_name, row.total) for row in used_result]

        free_list = subtract_quantities(capacity_list, used_list)

        return ResourceInfo(
            capacity=capacity_list,
            used=used_list,
            free=free_list,
        )

    # =========================================================================
    # Allow / Disallow (atomic add+remove in single read-committed transaction)
    # =========================================================================

    async def update_allowed_resource_groups_for_domain(
        self,
        domain_name: str,
        add: list[ResourceGroupID],
        remove: list[ResourceGroupID],
    ) -> list[str]:
        """Atomically add/remove allowed resource groups for a domain.

        Alongside the N:N mapping rows, maintains the domain scope's RBAC association
        with each resource group (association row + membership + virtual-entity binding).

        Returns the current list of allowed resource group names after the update.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            domain_id = await self._get_domain_id(w, domain_name)
            domain_scope = ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id)
            if remove:
                await w.batch_purge(
                    BatchPurger(
                        spec=ResourceGroupsForDomainPurgerSpec(
                            resource_group_ids=list(remove),
                            domain_id=domain_id,
                        )
                    )
                )
                await self._withdraw_resource_groups(w, domain_scope, list(remove))

            if add:
                creation_result = await w.bulk_create_partial(
                    BulkCreator(
                        specs=[
                            ResourceGroupForDomainCreatorSpec(
                                resource_group_id=rg_id,
                                domain_id=domain_id,
                            )
                            for rg_id in add
                        ]
                    )
                )
                self._tolerate_only_duplicates(creation_result)
                await self._enroll_resource_groups(w, domain_scope, list(add))

            result = await w.batch_query_in_global(
                sa.select(ResourceGroupRow.name)
                .join(
                    ResourceGroupForDomainRow,
                    ResourceGroupForDomainRow.resource_group_id == ResourceGroupRow.id,
                )
                .where(ResourceGroupForDomainRow.domain_id == domain_id),
                BatchQuerier(pagination=NoPagination()),
            )
            return [row.name for row in result.rows]

    async def update_allowed_resource_groups_for_project(
        self,
        project_id: uuid.UUID,
        add: list[ResourceGroupID],
        remove: list[ResourceGroupID],
    ) -> list[str]:
        """Atomically add/remove allowed resource groups for a project.

        Alongside the N:N mapping rows, maintains the project scope's RBAC association
        with each resource group (association row + membership + virtual-entity binding).

        Returns the current list of allowed resource group names after the update.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            project_scope = ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(project_id))
            if remove:
                await w.batch_purge(
                    BatchPurger(
                        spec=ResourceGroupsForProjectPurgerSpec(
                            resource_group_ids=list(remove),
                            project=project_id,
                        )
                    )
                )
                await self._withdraw_resource_groups(w, project_scope, list(remove))

            if add:
                creation_result = await w.bulk_create_partial(
                    BulkCreator(
                        specs=[
                            ResourceGroupForProjectCreatorSpec(
                                resource_group_id=rg_id,
                                project=project_id,
                            )
                            for rg_id in add
                        ]
                    )
                )
                self._tolerate_only_duplicates(creation_result)
                await self._enroll_resource_groups(w, project_scope, list(add))

            result = await w.batch_query_in_global(
                sa.select(ResourceGroupRow.name)
                .join(
                    ResourceGroupForProjectRow,
                    ResourceGroupForProjectRow.resource_group_id == ResourceGroupRow.id,
                )
                .where(ResourceGroupForProjectRow.group == project_id),
                BatchQuerier(pagination=NoPagination()),
            )
            return [row.name for row in result.rows]

    async def update_allowed_domains_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
        add: list[str],
        remove: list[str],
    ) -> list[str]:
        """Atomically add/remove allowed domains for a resource group.

        Returns the current list of allowed domain names after the update.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            domain_ids_by_name = await self._get_domain_ids_by_names(w, [*add, *remove])
            if remove:
                remove_ids = [
                    domain_ids_by_name[name] for name in remove if name in domain_ids_by_name
                ]
                await w.batch_purge(
                    BatchPurger(
                        spec=DomainsForResourceGroupPurgerSpec(
                            resource_group_id=resource_group_id,
                            domain_ids=remove_ids,
                        )
                    )
                )
                for domain_id in remove_ids:
                    await self._withdraw_resource_groups(
                        w,
                        ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id),
                        [resource_group_id],
                    )

            if add:
                add_ids: list[DomainID] = []
                for domain_name in add:
                    added_domain_id = domain_ids_by_name.get(domain_name)
                    if added_domain_id is None:
                        raise DomainNotFound(f"Domain '{domain_name}' not found")
                    add_ids.append(added_domain_id)
                creation_result = await w.bulk_create_partial(
                    BulkCreator(
                        specs=[
                            ResourceGroupForDomainCreatorSpec(
                                resource_group_id=resource_group_id,
                                domain_id=domain_id,
                            )
                            for domain_id in add_ids
                        ]
                    )
                )
                self._tolerate_only_duplicates(creation_result)
                for domain_id in add_ids:
                    await self._enroll_resource_groups(
                        w,
                        ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id),
                        [resource_group_id],
                    )

            result = await w.batch_query_in_global(
                sa.select(DomainRow.name)
                .join(
                    ResourceGroupForDomainRow,
                    ResourceGroupForDomainRow.domain_id == DomainRow.id,
                )
                .where(ResourceGroupForDomainRow.resource_group_id == resource_group_id),
                BatchQuerier(pagination=NoPagination()),
            )
            return [row.name for row in result.rows]

    async def update_allowed_projects_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
        add: list[uuid.UUID],
        remove: list[uuid.UUID],
    ) -> list[uuid.UUID]:
        """Atomically add/remove allowed projects for a resource group.

        Returns the current list of allowed project IDs after the update.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            if remove:
                await w.batch_purge(
                    BatchPurger(
                        spec=ProjectsForResourceGroupPurgerSpec(
                            resource_group_id=resource_group_id,
                            project_ids=[ProjectID(project_id) for project_id in remove],
                        )
                    )
                )
                for project_id in remove:
                    await self._withdraw_resource_groups(
                        w,
                        ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(project_id)),
                        [resource_group_id],
                    )

            if add:
                creation_result = await w.bulk_create_partial(
                    BulkCreator(
                        specs=[
                            ResourceGroupForProjectCreatorSpec(
                                resource_group_id=resource_group_id,
                                project=project_id,
                            )
                            for project_id in add
                        ]
                    )
                )
                self._tolerate_only_duplicates(creation_result)
                for project_id in add:
                    await self._enroll_resource_groups(
                        w,
                        ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(project_id)),
                        [resource_group_id],
                    )

            result = await w.batch_query_in_global(
                sa.select(ResourceGroupForProjectRow.group).where(
                    ResourceGroupForProjectRow.resource_group_id == resource_group_id
                ),
                BatchQuerier(pagination=NoPagination()),
            )
            return [row.group for row in result.rows]

    # =========================================================================
    # Get allowed (read-only queries)
    # =========================================================================

    async def get_allowed_domains_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
    ) -> list[str]:
        """Get allowed domain names for a resource group."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(DomainRow.name)
                .join(
                    ResourceGroupForDomainRow,
                    ResourceGroupForDomainRow.domain_id == DomainRow.id,
                )
                .where(ResourceGroupForDomainRow.resource_group_id == resource_group_id)
            )
            return [row[0] for row in result]

    async def get_allowed_projects_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
    ) -> list[uuid.UUID]:
        """Get allowed project IDs for a resource group."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(ResourceGroupForProjectRow.group).where(
                    ResourceGroupForProjectRow.resource_group_id == resource_group_id
                )
            )
            return [row[0] for row in result]
