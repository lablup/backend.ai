from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.base import (
    GUID,
    Base,
    ResourceSlotColumn,
)

__all__: Sequence[str] = ("resource_presets",)


class ResourcePresetRow(Base):
    __tablename__ = "resource_presets"
    id: Mapped[ResourcePresetID] = mapped_column(
        "id", GUID(ResourcePresetID), primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=256), nullable=False)
    resource_slots: Mapped[ResourceSlot] = mapped_column(
        "resource_slots", ResourceSlotColumn(), nullable=False
    )
    shared_memory: Mapped[int | None] = mapped_column(
        "shared_memory", sa.BigInteger(), nullable=True
    )

    # If `scaling_group_name` is None, the preset is global
    scaling_group_name: Mapped[str | None] = mapped_column(
        "scaling_group_name", sa.String(length=64), nullable=True, server_default=sa.null()
    )
    __table_args__ = (
        sa.Index(
            "ix_resource_presets_name_null_scaling_group_name",
            name,
            postgresql_where=scaling_group_name.is_(None),
            unique=True,
        ),
        sa.Index(
            "ix_resource_presets_name_scaling_group_name",
            name,
            scaling_group_name,
            postgresql_where=scaling_group_name.isnot(None),
            unique=True,
        ),
    )


# Used only by batch_load_by_name in gql_legacy.
resource_presets = ResourcePresetRow.__table__
