from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec


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
