from __future__ import annotations

from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.scaling_group import ScalingGroupForKeypairsRow
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec


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
