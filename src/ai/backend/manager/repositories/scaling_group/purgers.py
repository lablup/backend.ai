from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec, PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class ScalingGroupPurgerSpec(PurgerSpec[ScalingGroupRow]):
    """PurgerSpec for deleting a scaling group."""

    name: str

    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ScalingGroupForDomainPurgerSpec(BatchPurgerSpec[ScalingGroupForDomainRow]):
    """PurgerSpec for disassociating a scaling group from a domain."""

    resource_group_id: ResourceGroupID
    domain_id: DomainID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForDomainRow]]:
        return sa.select(ScalingGroupForDomainRow).where(
            sa.and_(
                ScalingGroupForDomainRow.scaling_group_id == self.resource_group_id,
                ScalingGroupForDomainRow.domain_id == self.domain_id,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ScalingGroupsForDomainPurgerSpec(BatchPurgerSpec[ScalingGroupForDomainRow]):
    """PurgerSpec for disassociating multiple scaling groups from a domain."""

    resource_group_ids: list[ResourceGroupID]
    domain_id: DomainID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForDomainRow]]:
        return sa.select(ScalingGroupForDomainRow).where(
            sa.and_(
                ScalingGroupForDomainRow.scaling_group_id.in_(self.resource_group_ids),
                ScalingGroupForDomainRow.domain_id == self.domain_id,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class AllScalingGroupsForDomainPurgerSpec(BatchPurgerSpec[ScalingGroupForDomainRow]):
    """PurgerSpec for disassociating all scaling groups from a domain."""

    domain_id: DomainID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForDomainRow]]:
        return sa.select(ScalingGroupForDomainRow).where(
            ScalingGroupForDomainRow.domain_id == self.domain_id,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ScalingGroupForKeypairsPurgerSpec(BatchPurgerSpec[ScalingGroupForKeypairsRow]):
    """PurgerSpec for disassociating a scaling group from a keypair."""

    resource_group_id: ResourceGroupID
    access_key: AccessKey

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForKeypairsRow]]:
        return sa.select(ScalingGroupForKeypairsRow).where(
            sa.and_(
                ScalingGroupForKeypairsRow.scaling_group_id == self.resource_group_id,
                ScalingGroupForKeypairsRow.access_key == self.access_key,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ScalingGroupsForKeypairsPurgerSpec(BatchPurgerSpec[ScalingGroupForKeypairsRow]):
    """PurgerSpec for disassociating multiple scaling groups from a keypair."""

    resource_group_ids: list[ResourceGroupID]
    access_key: AccessKey

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForKeypairsRow]]:
        return sa.select(ScalingGroupForKeypairsRow).where(
            sa.and_(
                ScalingGroupForKeypairsRow.scaling_group_id.in_(self.resource_group_ids),
                ScalingGroupForKeypairsRow.access_key == self.access_key,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


def create_scaling_group_for_domain_purger(
    resource_group_id: ResourceGroupID,
    domain_id: DomainID,
) -> BatchPurger[ScalingGroupForDomainRow]:
    """Create a BatchPurger for disassociating a scaling group from a domain."""
    return BatchPurger(
        spec=ScalingGroupForDomainPurgerSpec(
            resource_group_id=resource_group_id,
            domain_id=domain_id,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )


def create_scaling_group_for_keypairs_purger(
    resource_group_id: ResourceGroupID,
    access_key: AccessKey,
) -> BatchPurger[ScalingGroupForKeypairsRow]:
    """Create a BatchPurger for disassociating a scaling group from a keypair."""
    return BatchPurger(
        spec=ScalingGroupForKeypairsPurgerSpec(
            resource_group_id=resource_group_id,
            access_key=access_key,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )


@dataclass
class ScalingGroupForProjectPurgerSpec(BatchPurgerSpec[ScalingGroupForProjectRow]):
    """PurgerSpec for disassociating a scaling group from a project (user group)."""

    resource_group_id: ResourceGroupID
    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForProjectRow]]:
        return sa.select(ScalingGroupForProjectRow).where(
            sa.and_(
                ScalingGroupForProjectRow.scaling_group_id == self.resource_group_id,
                ScalingGroupForProjectRow.group == self.project,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ScalingGroupsForProjectPurgerSpec(BatchPurgerSpec[ScalingGroupForProjectRow]):
    """PurgerSpec for disassociating multiple scaling groups from a project (user group)."""

    resource_group_ids: list[ResourceGroupID]
    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForProjectRow]]:
        return sa.select(ScalingGroupForProjectRow).where(
            sa.and_(
                ScalingGroupForProjectRow.scaling_group_id.in_(self.resource_group_ids),
                ScalingGroupForProjectRow.group == self.project,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class AllScalingGroupsForProjectPurgerSpec(BatchPurgerSpec[ScalingGroupForProjectRow]):
    """PurgerSpec for disassociating all scaling groups from a project (user group)."""

    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForProjectRow]]:
        return sa.select(ScalingGroupForProjectRow).where(
            ScalingGroupForProjectRow.group == self.project,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


def create_scaling_group_for_project_purger(
    resource_group_id: ResourceGroupID,
    project: UUID,
) -> BatchPurger[ScalingGroupForProjectRow]:
    """Create a BatchPurger for disassociating a scaling group from a project."""
    return BatchPurger(
        spec=ScalingGroupForProjectPurgerSpec(
            resource_group_id=resource_group_id,
            project=project,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )
