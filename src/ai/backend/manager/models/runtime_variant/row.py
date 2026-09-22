from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.manager.models.base import GUID, Base, PydanticColumn
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("RuntimeVariantRow",)


class RuntimeVariantRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "runtime_variants"

    id: Mapped[RuntimeVariantID] = mapped_column(
        "id",
        GUID(RuntimeVariantID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    reads_vfolder_config_files: Mapped[bool] = mapped_column(
        "reads_vfolder_config_files",
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
    )
    default_model_definition: Mapped[DefaultModelDefinition] = mapped_column(
        "default_model_definition",
        PydanticColumn(DefaultModelDefinition, exclude_unset=True),
        nullable=False,
    )
