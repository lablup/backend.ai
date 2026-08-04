"""Database source for scaling group repository operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, cast

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.resource_group import (
    RESOURCE_GROUP_ENTITY_TYPE,
    RESOURCE_GROUP_SCOPE_TYPE,
)
from ai.backend.common.data.entity.types import EntityRef, ScopeRef, ScopeType
from ai.backend.common.exception import DomainNotFound
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.types import SlotQuantity
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.scaling_group.types import (
    ResourceInfo,
    ScalingGroupData,
    ScalingGroupListResult,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
    query_allowed_sgroups,
)
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    BulkCreatorResultWithFailures,
    Creator,
    execute_bulk_creator,
)
from ai.backend.manager.repositories.base.pagination import NoPagination
from ai.backend.manager.repositories.base.purger import (
    BatchPurger,
    Purger,
    execute_batch_purger,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.base.rbac.scope_binder import RBACScopeBinder
from ai.backend.manager.repositories.base.rbac.scope_unbinder import RBACScopeEntityUnbinder
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    RBACOpsProvider,
    RBACWriteOps,
    ScopeDeletion,
    ScopeEntityMember,
)
from ai.backend.manager.repositories.resource_slot.types import subtract_quantities
from ai.backend.manager.repositories.scaling_group.creators import (
    ResourceGroupScopeCreation,
    ScalingGroupCreatorSpec,
    ScalingGroupForDomainCreatorSpec,
    ScalingGroupForProjectCreatorSpec,
)
from ai.backend.manager.repositories.scaling_group.purgers import (
    DomainsForScalingGroupPurgerSpec,
    ProjectsForScalingGroupPurgerSpec,
    ResourceGroupPurgerSpec,
    ScalingGroupEndpointsPurgerSpec,
    ScalingGroupKernelsPurgerSpec,
    ScalingGroupRoutingsPurgerSpec,
    ScalingGroupSessionsPurgerSpec,
    ScalingGroupsForDomainPurgerSpec,
    ScalingGroupsForProjectPurgerSpec,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = (
    "ScalingGroupDBSource",
    "ScalingGroupListResult",
)


class ScalingGroupDBSource:
    """
    Database source for scaling group operations.
    Handles all database operations for scaling groups.
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
            scope_type=ScopeType(ref.element_type.value),
            scope_id=uuid.UUID(ref.element_id),
        )

    def _raise_non_duplicate_errors[TRow: Base](
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

    async def _get_resource_group_id(
        self, w: RBACWriteOps, scaling_group_name: str
    ) -> ResourceGroupID:
        result = await w.batch_query_in_global(
            sa.select(ScalingGroupRow.id).where(ScalingGroupRow.name == scaling_group_name),
            BatchQuerier(pagination=NoPagination()),
        )
        if not result.rows:
            raise ScalingGroupNotFound(scaling_group_name)
        return ResourceGroupID(result.rows[0].id)

    async def create_scaling_group(
        self,
        creator: Creator[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Creates a new scaling group as a resource-group scope: the row is created
        together with its virtual scope, so RBAC resolution reaches the resource group
        and its entities through the virtual-scope chain.

        Raises ScalingGroupConflict if a scaling group with the same name already exists.
        """
        spec = cast(ScalingGroupCreatorSpec, creator.spec)
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.create_scope(ResourceGroupScopeCreation(spec=spec))
            return result.row.to_dataclass()

    async def search_scaling_groups(
        self,
        querier: BatchQuerier,
    ) -> ScalingGroupListResult:
        """Searches scaling groups with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ScalingGroupRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.ScalingGroupRow.to_dataclass() for row in result.rows]

            return ScalingGroupListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def get_resource_group_id_by_name(self, name: ResourceGroupName) -> ResourceGroupID:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ScalingGroupRow.id).where(ScalingGroupRow.name == name)
            resource_group_id = await db_sess.scalar(query)
            if resource_group_id is None:
                raise ScalingGroupNotFound(name)
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
                sa.select(ScalingGroupRow.name, ScalingGroupRow.id).where(
                    ScalingGroupRow.name.in_(names)
                )
            )
            return {ResourceGroupName(row.name): row.id for row in rows}

    async def get_scaling_group_by_name(
        self,
        name: str,
    ) -> ScalingGroupData:
        """Get a single scaling group by name (primary key).

        Args:
            name: The name of the scaling group (primary key).

        Returns:
            ScalingGroupData for the requested scaling group.

        Raises:
            ScalingGroupNotFound: If the scaling group does not exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.get(ScalingGroupRow, name)
            if row is None:
                raise ScalingGroupNotFound(name)
            return row.to_dataclass()

    async def purge_scaling_group(
        self,
        purger: Purger[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Purges a scaling group and all related sessions, routes, endpoints, and
        kernels, together with its RBAC entries and virtual scope.

        Raises ScalingGroupNotFound if scaling group doesn't exist.
        """
        scaling_group_name = cast(str, purger.spec.pk_value())
        async with self._rbac_ops_provider.write_ops() as w:
            resource_group_id = await self._get_resource_group_id(w, scaling_group_name)

            await w.batch_purge(
                BatchPurger(
                    spec=ScalingGroupRoutingsPurgerSpec(resource_group_id=resource_group_id)
                )
            )
            await w.batch_purge(
                BatchPurger(
                    spec=ScalingGroupEndpointsPurgerSpec(resource_group_id=resource_group_id)
                )
            )
            await w.batch_purge(
                BatchPurger(spec=ScalingGroupKernelsPurgerSpec(resource_group_id=resource_group_id))
            )
            await w.batch_purge(
                BatchPurger(
                    spec=ScalingGroupSessionsPurgerSpec(resource_group_id=resource_group_id)
                )
            )

            result = await w.delete_scope(
                ScopeDeletion(
                    purger=RBACEntityPurger(
                        spec=ResourceGroupPurgerSpec(
                            name=scaling_group_name,
                            resource_group_id=resource_group_id,
                        )
                    ),
                    scope=self._resource_group_scope(resource_group_id),
                )
            )
            if result is None:
                raise ScalingGroupNotFound(f"Scaling group not found (name:{scaling_group_name})")

            return result.row.to_dataclass()

    async def update_scaling_group(
        self,
        updater: Updater[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Updates an existing scaling group.

        Raises ScalingGroupNotFound if the scaling group does not exist.
        """
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise ScalingGroupNotFound(f"Scaling group not found (name:{updater.pk_value})")
            return result.row.to_dataclass()

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
            ScalingGroupNotFound: If the scaling group does not exist.
        """
        async with self._db.begin_session() as session:
            stmt = (
                sa.update(ScalingGroupRow)
                .where(ScalingGroupRow.name == name)
                .values(default_deployment_options=options)
                .returning(ScalingGroupRow.default_deployment_options)
            )
            result = await session.execute(stmt)
            row = result.first()
            if row is None:
                raise ScalingGroupNotFound(f"Scaling group not found (name:{name})")
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
            ScalingGroupNotFound: If the scaling group does not exist.
        """
        async with self._db.begin_session() as session:
            stmt = (
                sa.update(ScalingGroupRow)
                .where(ScalingGroupRow.name == name)
                .values(default_session_options=options)
                .returning(ScalingGroupRow.default_session_options)
            )
            result = await session.execute(stmt)
            row = result.first()
            if row is None:
                raise ScalingGroupNotFound(f"Scaling group not found (name:{name})")
            stored: DefaultSessionOptions = row[0]
            return stored

    async def associate_scaling_group_with_domains(
        self,
        binder: RBACScopeBinder[ScalingGroupForDomainRow],
    ) -> None:
        """Associates a scaling group with multiple domains, binding each domain scope
        to the resource group's virtual scope."""
        await self._associate_resource_groups(binder)

    async def disassociate_scaling_group_with_domains(
        self,
        unbinder: RBACScopeEntityUnbinder[ScalingGroupForDomainRow],
    ) -> None:
        """Disassociates scaling groups from a domain, unbinding the domain scope from
        each resource group's virtual scope."""
        await self._disassociate_resource_groups(unbinder)

    async def _associate_resource_groups[TRow: Base](self, binder: RBACScopeBinder[TRow]) -> None:
        """Create the N:N mapping rows and enroll each pair's resource group into the
        pair's scope (association row + membership), binding the scope to the resource
        group's virtual scope so it reaches the resource group's entities."""
        if not binder.pairs:
            return
        async with self._rbac_ops_provider.write_ops() as w:
            await w.bulk_create(BulkCreator(specs=[pair.spec for pair in binder.pairs]))
            for pair in binder.pairs:
                accessor_scope = self._scope_ref_of(pair.scope_ref)
                resource_group_id = ResourceGroupID(uuid.UUID(pair.entity_ref.element_id))
                await self._enroll_resource_group(w, accessor_scope, resource_group_id)

    async def _disassociate_resource_groups[TRow: Base](
        self, unbinder: RBACScopeEntityUnbinder[TRow]
    ) -> None:
        """Delete the N:N mapping rows and withdraw each resource group from the
        unbinder's scope (association row + membership + virtual-scope binding)."""
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

    async def _enroll_resource_group(
        self,
        w: RBACWriteOps,
        accessor_scope: ScopeRef,
        resource_group_id: ResourceGroupID,
    ) -> None:
        """Enroll a resource group into ``accessor_scope`` with existing RBAC ops:
        membership + association row via ``add_entity_members``, and the reverse
        ``accessor_scope`` binding to the resource group's virtual scope via
        ``ensure_scope`` (created lazily for pre-virtual-scope rows)."""
        await w.ensure_scope(accessor_scope)
        await w.add_entity_members(
            EntityMembersAddition(
                scope=accessor_scope,
                members=[ScopeEntityMember(ref=self._resource_group_entity(resource_group_id))],
            )
        )
        await w.ensure_scope(
            self._resource_group_scope(resource_group_id), bound_scope=accessor_scope
        )

    async def _withdraw_resource_groups(
        self,
        w: RBACWriteOps,
        accessor_scope: ScopeRef,
        resource_group_ids: list[ResourceGroupID],
    ) -> None:
        """Withdraw resource groups from ``accessor_scope``: memberships + association
        rows via ``remove_entity_members``, and the reverse scope bindings via
        ``unbind_scope``. Each resource group's virtual scope is ensured first, since
        ``unbind_scope`` requires it and pre-virtual-scope rows may not have one."""
        if not resource_group_ids:
            return
        await w.remove_entity_members(
            accessor_scope,
            [self._resource_group_entity(rg_id) for rg_id in resource_group_ids],
        )
        for rg_id in resource_group_ids:
            resource_group_scope = self._resource_group_scope(rg_id)
            await w.ensure_scope(resource_group_scope)
            await w.unbind_scope(accessor_scope, resource_group_scope)

    async def check_scaling_group_domain_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        domain_id: DomainID,
    ) -> bool:
        """Checks if a scaling group is associated with a domain."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(ScalingGroupForDomainRow)
                .where(
                    sa.and_(
                        ScalingGroupForDomainRow.resource_group_id == resource_group_id,
                        ScalingGroupForDomainRow.domain_id == domain_id,
                    )
                )
            )
            result = await session.scalar(query)
            return (result or 0) > 0

    async def associate_scaling_group_with_keypairs(
        self,
        bulk_creator: BulkCreator[ScalingGroupForKeypairsRow],
    ) -> None:
        """Associates a scaling group with multiple keypairs."""
        async with self._db.begin_session() as session:
            await execute_bulk_creator(session, bulk_creator)

    async def disassociate_scaling_group_with_keypairs(
        self,
        purger: BatchPurger[ScalingGroupForKeypairsRow],
    ) -> None:
        """Disassociates a scaling group from multiple keypairs."""
        async with self._db.begin_session() as session:
            await execute_batch_purger(session, purger)

    async def check_scaling_group_keypair_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        access_key: str,
    ) -> bool:
        """Checks if a scaling group is associated with a keypair."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(
                sa.exists().where(
                    sa.and_(
                        ScalingGroupForKeypairsRow.resource_group_id == resource_group_id,
                        ScalingGroupForKeypairsRow.access_key == access_key,
                    )
                )
            )
            result = await session.execute(query)
            return result.scalar() or False

    async def associate_scaling_group_with_user_groups(
        self,
        binder: RBACScopeBinder[ScalingGroupForProjectRow],
    ) -> None:
        """Associates a scaling group with multiple user groups (projects), binding each
        project scope to the resource group's virtual scope."""
        await self._associate_resource_groups(binder)

    async def disassociate_scaling_group_with_user_groups(
        self,
        unbinder: RBACScopeEntityUnbinder[ScalingGroupForProjectRow],
    ) -> None:
        """Disassociates scaling groups from a project, unbinding the project scope from
        each resource group's virtual scope."""
        await self._disassociate_resource_groups(unbinder)

    async def check_scaling_group_user_group_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        user_group: uuid.UUID,
    ) -> bool:
        """Checks if a scaling group is associated with a user group (project)."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(ScalingGroupForProjectRow)
                .where(
                    sa.and_(
                        ScalingGroupForProjectRow.resource_group_id == resource_group_id,
                        ScalingGroupForProjectRow.group == user_group,
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
    ) -> list[ScalingGroupData]:
        """List allowed scaling groups for a user using the legacy query_allowed_sgroups function.

        Returns ScalingGroupData for each allowed scaling group.
        """
        async with self._db.begin_readonly() as conn:
            rows = await query_allowed_sgroups(conn, domain_name, group, access_key)
            # Convert raw rows to ScalingGroupData via ORM
            sg_names = [row.name for row in rows]

        if not sg_names:
            return []

        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(ScalingGroupRow)
                .where(ScalingGroupRow.name.in_(sg_names))
                .order_by(ScalingGroupRow.name)
            )
            result = await db_sess.execute(query)
            return [row.to_dataclass() for row in result.scalars()]

    async def get_resource_info(
        self,
        scaling_group: str,
    ) -> ResourceInfo:
        """Get aggregated resource information for a scaling group.

        Uses normalized agent_resources table with SQL-level aggregation.

        Args:
            scaling_group: The name of the scaling group.

        Returns:
            ResourceInfo containing capacity, used, and free resource metrics.

        Raises:
            ScalingGroupNotFound: If the scaling group does not exist.
        """
        ar = AgentResourceRow.__table__
        ag = AgentRow.__table__
        rst = ResourceSlotTypeRow.__table__

        async with self._db.begin_readonly_session() as db_sess:
            # Validate scaling group exists
            sg_exists = await db_sess.scalar(
                sa.select(sa.exists().where(ScalingGroupRow.name == scaling_group))
            )
            if not sg_exists:
                raise ScalingGroupNotFound(scaling_group)

            # Capacity: ALIVE + schedulable agents, JOIN rst for rank ordering
            capacity_stmt = (
                sa.select(ar.c.slot_name, sa.func.sum(ar.c.capacity).label("total"))
                .select_from(
                    ar.join(ag, ar.c.agent_id == ag.c.id).join(
                        rst, ar.c.slot_name == rst.c.slot_name
                    )
                )
                .where(
                    ag.c.scaling_group == scaling_group,
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
                    ag.c.scaling_group == scaling_group,
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
        with each resource group (association row + membership + virtual-scope binding).

        Returns the current list of allowed resource group names after the update.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            domain_id = await self._get_domain_id(w, domain_name)
            domain_scope = ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id)
            if remove:
                await w.batch_purge(
                    BatchPurger(
                        spec=ScalingGroupsForDomainPurgerSpec(
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
                            ScalingGroupForDomainCreatorSpec(
                                resource_group_id=rg_id,
                                domain_id=domain_id,
                            )
                            for rg_id in add
                        ]
                    )
                )
                self._raise_non_duplicate_errors(creation_result)
                for rg_id in add:
                    await self._enroll_resource_group(w, domain_scope, rg_id)

            result = await w.batch_query_in_global(
                sa.select(ScalingGroupRow.name)
                .join(
                    ScalingGroupForDomainRow,
                    ScalingGroupForDomainRow.resource_group_id == ScalingGroupRow.id,
                )
                .where(ScalingGroupForDomainRow.domain_id == domain_id),
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
        with each resource group (association row + membership + virtual-scope binding).

        Returns the current list of allowed resource group names after the update.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            project_scope = ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(project_id))
            if remove:
                await w.batch_purge(
                    BatchPurger(
                        spec=ScalingGroupsForProjectPurgerSpec(
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
                            ScalingGroupForProjectCreatorSpec(
                                resource_group_id=rg_id,
                                project=project_id,
                            )
                            for rg_id in add
                        ]
                    )
                )
                self._raise_non_duplicate_errors(creation_result)
                for rg_id in add:
                    await self._enroll_resource_group(w, project_scope, rg_id)

            result = await w.batch_query_in_global(
                sa.select(ScalingGroupRow.name)
                .join(
                    ScalingGroupForProjectRow,
                    ScalingGroupForProjectRow.resource_group_id == ScalingGroupRow.id,
                )
                .where(ScalingGroupForProjectRow.group == project_id),
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
                        spec=DomainsForScalingGroupPurgerSpec(
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
                            ScalingGroupForDomainCreatorSpec(
                                resource_group_id=resource_group_id,
                                domain_id=domain_id,
                            )
                            for domain_id in add_ids
                        ]
                    )
                )
                self._raise_non_duplicate_errors(creation_result)
                for domain_id in add_ids:
                    await self._enroll_resource_group(
                        w,
                        ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id),
                        resource_group_id,
                    )

            result = await w.batch_query_in_global(
                sa.select(DomainRow.name)
                .join(
                    ScalingGroupForDomainRow,
                    ScalingGroupForDomainRow.domain_id == DomainRow.id,
                )
                .where(ScalingGroupForDomainRow.resource_group_id == resource_group_id),
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
                        spec=ProjectsForScalingGroupPurgerSpec(
                            resource_group_id=resource_group_id,
                            projects=list(remove),
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
                            ScalingGroupForProjectCreatorSpec(
                                resource_group_id=resource_group_id,
                                project=project_id,
                            )
                            for project_id in add
                        ]
                    )
                )
                self._raise_non_duplicate_errors(creation_result)
                for project_id in add:
                    await self._enroll_resource_group(
                        w,
                        ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(project_id)),
                        resource_group_id,
                    )

            result = await w.batch_query_in_global(
                sa.select(ScalingGroupForProjectRow.group).where(
                    ScalingGroupForProjectRow.resource_group_id == resource_group_id
                ),
                BatchQuerier(pagination=NoPagination()),
            )
            return [row.group for row in result.rows]

    # =========================================================================
    # Get allowed (read-only queries)
    # =========================================================================

    async def get_allowed_resource_groups_for_domain(
        self,
        domain_name: str,
    ) -> list[str]:
        """Get allowed resource group names for a domain."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(ScalingGroupRow.name)
                .join(
                    ScalingGroupForDomainRow,
                    ScalingGroupForDomainRow.resource_group_id == ScalingGroupRow.id,
                )
                .join(DomainRow, DomainRow.id == ScalingGroupForDomainRow.domain_id)
                .where(DomainRow.name == domain_name)
            )
            return [row[0] for row in result]

    async def get_allowed_resource_groups_for_project(
        self,
        project_id: uuid.UUID,
    ) -> list[str]:
        """Get allowed resource group names for a project."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(ScalingGroupRow.name)
                .join(
                    ScalingGroupForProjectRow,
                    ScalingGroupForProjectRow.resource_group_id == ScalingGroupRow.id,
                )
                .where(ScalingGroupForProjectRow.group == project_id)
            )
            return [row[0] for row in result]

    async def get_allowed_domains_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
    ) -> list[str]:
        """Get allowed domain names for a resource group."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(DomainRow.name)
                .join(
                    ScalingGroupForDomainRow,
                    ScalingGroupForDomainRow.domain_id == DomainRow.id,
                )
                .where(ScalingGroupForDomainRow.resource_group_id == resource_group_id)
            )
            return [row[0] for row in result]

    async def get_allowed_projects_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
    ) -> list[uuid.UUID]:
        """Get allowed project IDs for a resource group."""
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                sa.select(ScalingGroupForProjectRow.group).where(
                    ScalingGroupForProjectRow.resource_group_id == resource_group_id
                )
            )
            return [row[0] for row in result]
