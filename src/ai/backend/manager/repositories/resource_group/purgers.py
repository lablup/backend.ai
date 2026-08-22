from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec, PurgerSpec
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurgerSpec


@dataclass
class ResourceGroupNamePurgerSpec(PurgerSpec[ResourceGroupRow]):
    """PurgerSpec for deleting a resource group by its name."""

    name: str

    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupPurgerSpec(RBACEntityPurgerSpec[ResourceGroupRow]):
    """PurgerSpec for purging a resource group together with its RBAC entries."""

    name: str
    resource_group_id: ResourceGroupID

    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.RESOURCE_GROUP

    @override
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.RESOURCE_GROUP,
            element_id=str(self.resource_group_id),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupRoutingsPurgerSpec(BatchPurgerSpec[RoutingRow]):
    """PurgerSpec for deleting the routings of a resource group's sessions."""

    resource_group_id: ResourceGroupID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[RoutingRow]]:
        return sa.select(RoutingRow).where(
            RoutingRow.session.in_(
                sa.select(SessionRow.id).where(
                    SessionRow.resource_group_id == self.resource_group_id
                )
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupEndpointsPurgerSpec(BatchPurgerSpec[EndpointRow]):
    """PurgerSpec for deleting the endpoints of a resource group.

    ``endpoints.resource_group`` stores the resource group name, so the id is
    resolved to the name with a subquery."""

    resource_group_id: ResourceGroupID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[EndpointRow]]:
        return sa.select(EndpointRow).where(
            EndpointRow.resource_group
            == sa.select(ResourceGroupRow.name)
            .where(ResourceGroupRow.id == self.resource_group_id)
            .scalar_subquery()
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupKernelsPurgerSpec(BatchPurgerSpec[KernelRow]):
    """PurgerSpec for deleting the kernels of a resource group's sessions."""

    resource_group_id: ResourceGroupID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[KernelRow]]:
        return sa.select(KernelRow).where(
            KernelRow.session_id.in_(
                sa.select(SessionRow.id).where(
                    SessionRow.resource_group_id == self.resource_group_id
                )
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupSessionsPurgerSpec(BatchPurgerSpec[SessionRow]):
    """PurgerSpec for deleting the sessions of a resource group."""

    resource_group_id: ResourceGroupID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionRow]]:
        return sa.select(SessionRow).where(SessionRow.resource_group_id == self.resource_group_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupForDomainPurgerSpec(BatchPurgerSpec[ResourceGroupForDomainRow]):
    """PurgerSpec for disassociating a resource group from a domain."""

    resource_group_id: ResourceGroupID
    domain_id: DomainID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForDomainRow]]:
        return sa.select(ResourceGroupForDomainRow).where(
            sa.and_(
                ResourceGroupForDomainRow.resource_group_id == self.resource_group_id,
                ResourceGroupForDomainRow.domain_id == self.domain_id,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupsForDomainPurgerSpec(BatchPurgerSpec[ResourceGroupForDomainRow]):
    """PurgerSpec for disassociating multiple resource groups from a domain."""

    resource_group_ids: list[ResourceGroupID]
    domain_id: DomainID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForDomainRow]]:
        return sa.select(ResourceGroupForDomainRow).where(
            sa.and_(
                ResourceGroupForDomainRow.resource_group_id.in_(self.resource_group_ids),
                ResourceGroupForDomainRow.domain_id == self.domain_id,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class DomainsForResourceGroupPurgerSpec(BatchPurgerSpec[ResourceGroupForDomainRow]):
    """PurgerSpec for disassociating multiple domains from a resource group."""

    resource_group_id: ResourceGroupID
    domain_ids: list[DomainID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForDomainRow]]:
        return sa.select(ResourceGroupForDomainRow).where(
            sa.and_(
                ResourceGroupForDomainRow.resource_group_id == self.resource_group_id,
                ResourceGroupForDomainRow.domain_id.in_(self.domain_ids),
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class AllResourceGroupsForDomainPurgerSpec(BatchPurgerSpec[ResourceGroupForDomainRow]):
    """PurgerSpec for disassociating all resource groups from a domain."""

    domain_id: DomainID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForDomainRow]]:
        return sa.select(ResourceGroupForDomainRow).where(
            ResourceGroupForDomainRow.domain_id == self.domain_id,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupForKeypairsPurgerSpec(BatchPurgerSpec[ResourceGroupForKeypairsRow]):
    """PurgerSpec for disassociating a resource group from a keypair."""

    resource_group_id: ResourceGroupID
    access_key: AccessKey

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForKeypairsRow]]:
        return sa.select(ResourceGroupForKeypairsRow).where(
            sa.and_(
                ResourceGroupForKeypairsRow.resource_group_id == self.resource_group_id,
                ResourceGroupForKeypairsRow.access_key == self.access_key,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupsForKeypairsPurgerSpec(BatchPurgerSpec[ResourceGroupForKeypairsRow]):
    """PurgerSpec for disassociating multiple resource groups from a keypair."""

    resource_group_ids: list[ResourceGroupID]
    access_key: AccessKey

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForKeypairsRow]]:
        return sa.select(ResourceGroupForKeypairsRow).where(
            sa.and_(
                ResourceGroupForKeypairsRow.resource_group_id.in_(self.resource_group_ids),
                ResourceGroupForKeypairsRow.access_key == self.access_key,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


def create_resource_group_for_domain_purger(
    resource_group_id: ResourceGroupID,
    domain_id: DomainID,
) -> BatchPurger[ResourceGroupForDomainRow]:
    """Create a BatchPurger for disassociating a resource group from a domain."""
    return BatchPurger(
        spec=ResourceGroupForDomainPurgerSpec(
            resource_group_id=resource_group_id,
            domain_id=domain_id,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )


def create_resource_group_for_keypairs_purger(
    resource_group_id: ResourceGroupID,
    access_key: AccessKey,
) -> BatchPurger[ResourceGroupForKeypairsRow]:
    """Create a BatchPurger for disassociating a resource group from a keypair."""
    return BatchPurger(
        spec=ResourceGroupForKeypairsPurgerSpec(
            resource_group_id=resource_group_id,
            access_key=access_key,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )


@dataclass
class ResourceGroupForProjectPurgerSpec(BatchPurgerSpec[ResourceGroupForProjectRow]):
    """PurgerSpec for disassociating a resource group from a project (user group)."""

    resource_group_id: ResourceGroupID
    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForProjectRow]]:
        return sa.select(ResourceGroupForProjectRow).where(
            sa.and_(
                ResourceGroupForProjectRow.resource_group_id == self.resource_group_id,
                ResourceGroupForProjectRow.group == self.project,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupsForProjectPurgerSpec(BatchPurgerSpec[ResourceGroupForProjectRow]):
    """PurgerSpec for disassociating multiple resource groups from a project (user group)."""

    resource_group_ids: list[ResourceGroupID]
    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForProjectRow]]:
        return sa.select(ResourceGroupForProjectRow).where(
            sa.and_(
                ResourceGroupForProjectRow.resource_group_id.in_(self.resource_group_ids),
                ResourceGroupForProjectRow.group == self.project,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ProjectsForResourceGroupPurgerSpec(BatchPurgerSpec[ResourceGroupForProjectRow]):
    """PurgerSpec for disassociating multiple projects from a resource group."""

    resource_group_id: ResourceGroupID
    project_ids: list[ProjectID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForProjectRow]]:
        return sa.select(ResourceGroupForProjectRow).where(
            sa.and_(
                ResourceGroupForProjectRow.resource_group_id == self.resource_group_id,
                ResourceGroupForProjectRow.group.in_(self.project_ids),
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class AllResourceGroupsForProjectPurgerSpec(BatchPurgerSpec[ResourceGroupForProjectRow]):
    """PurgerSpec for disassociating all resource groups from a project (user group)."""

    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForProjectRow]]:
        return sa.select(ResourceGroupForProjectRow).where(
            ResourceGroupForProjectRow.group == self.project,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


def create_resource_group_for_project_purger(
    resource_group_id: ResourceGroupID,
    project: UUID,
) -> BatchPurger[ResourceGroupForProjectRow]:
    """Create a BatchPurger for disassociating a resource group from a project."""
    return BatchPurger(
        spec=ResourceGroupForProjectPurgerSpec(
            resource_group_id=resource_group_id,
            project=project,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )
