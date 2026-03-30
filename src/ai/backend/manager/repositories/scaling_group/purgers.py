from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec


@dataclass
class ScalingGroupForDomainPurgerSpec(BatchPurgerSpec[ScalingGroupForDomainRow]):
    """PurgerSpec for disassociating a scaling group from a domain."""

    scaling_group: str
    domain: str

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForDomainRow]]:
        return sa.select(ScalingGroupForDomainRow).where(
            sa.and_(
                ScalingGroupForDomainRow.scaling_group == self.scaling_group,
                ScalingGroupForDomainRow.domain == self.domain,
            )
        )


@dataclass
class ScalingGroupsForDomainPurgerSpec(BatchPurgerSpec[ScalingGroupForDomainRow]):
    """PurgerSpec for disassociating multiple scaling groups from a domain."""

    scaling_groups: list[str]
    domain: str

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForDomainRow]]:
        return sa.select(ScalingGroupForDomainRow).where(
            sa.and_(
                ScalingGroupForDomainRow.scaling_group.in_(self.scaling_groups),
                ScalingGroupForDomainRow.domain == self.domain,
            )
        )


@dataclass
class AllScalingGroupsForDomainPurgerSpec(BatchPurgerSpec[ScalingGroupForDomainRow]):
    """PurgerSpec for disassociating all scaling groups from a domain."""

    domain: str

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForDomainRow]]:
        return sa.select(ScalingGroupForDomainRow).where(
            ScalingGroupForDomainRow.domain == self.domain,
        )


@dataclass
class ScalingGroupForKeypairsPurgerSpec(BatchPurgerSpec[ScalingGroupForKeypairsRow]):
    """PurgerSpec for disassociating a scaling group from a keypair."""

    scaling_group: str
    access_key: AccessKey

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForKeypairsRow]]:
        return sa.select(ScalingGroupForKeypairsRow).where(
            sa.and_(
                ScalingGroupForKeypairsRow.scaling_group == self.scaling_group,
                ScalingGroupForKeypairsRow.access_key == self.access_key,
            )
        )


@dataclass
class ScalingGroupsForKeypairsPurgerSpec(BatchPurgerSpec[ScalingGroupForKeypairsRow]):
    """PurgerSpec for disassociating multiple scaling groups from a keypair."""

    scaling_groups: list[str]
    access_key: AccessKey

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForKeypairsRow]]:
        return sa.select(ScalingGroupForKeypairsRow).where(
            sa.and_(
                ScalingGroupForKeypairsRow.scaling_group.in_(self.scaling_groups),
                ScalingGroupForKeypairsRow.access_key == self.access_key,
            )
        )


def create_scaling_group_for_domain_purger(
    scaling_group: str,
    domain: str,
) -> BatchPurger[ScalingGroupForDomainRow]:
    """Create a BatchPurger for disassociating a scaling group from a domain."""
    return BatchPurger(
        spec=ScalingGroupForDomainPurgerSpec(
            scaling_group=scaling_group,
            domain=domain,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )


def create_scaling_group_for_keypairs_purger(
    scaling_group: str,
    access_key: AccessKey,
) -> BatchPurger[ScalingGroupForKeypairsRow]:
    """Create a BatchPurger for disassociating a scaling group from a keypair."""
    return BatchPurger(
        spec=ScalingGroupForKeypairsPurgerSpec(
            scaling_group=scaling_group,
            access_key=access_key,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )


@dataclass
class ScalingGroupForProjectPurgerSpec(BatchPurgerSpec[ScalingGroupForProjectRow]):
    """PurgerSpec for disassociating a scaling group from a project (user group)."""

    scaling_group: str
    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForProjectRow]]:
        return sa.select(ScalingGroupForProjectRow).where(
            sa.and_(
                ScalingGroupForProjectRow.scaling_group == self.scaling_group,
                ScalingGroupForProjectRow.group == self.project,
            )
        )


@dataclass
class ScalingGroupsForProjectPurgerSpec(BatchPurgerSpec[ScalingGroupForProjectRow]):
    """PurgerSpec for disassociating multiple scaling groups from a project (user group)."""

    scaling_groups: list[str]
    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForProjectRow]]:
        return sa.select(ScalingGroupForProjectRow).where(
            sa.and_(
                ScalingGroupForProjectRow.scaling_group.in_(self.scaling_groups),
                ScalingGroupForProjectRow.group == self.project,
            )
        )


@dataclass
class AllScalingGroupsForProjectPurgerSpec(BatchPurgerSpec[ScalingGroupForProjectRow]):
    """PurgerSpec for disassociating all scaling groups from a project (user group)."""

    project: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ScalingGroupForProjectRow]]:
        return sa.select(ScalingGroupForProjectRow).where(
            ScalingGroupForProjectRow.group == self.project,
        )


def create_scaling_group_for_project_purger(
    scaling_group: str,
    project: UUID,
) -> BatchPurger[ScalingGroupForProjectRow]:
    """Create a BatchPurger for disassociating a scaling group from a project."""
    return BatchPurger(
        spec=ScalingGroupForProjectPurgerSpec(
            scaling_group=scaling_group,
            project=project,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )
