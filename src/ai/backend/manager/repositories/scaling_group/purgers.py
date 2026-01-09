from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
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
