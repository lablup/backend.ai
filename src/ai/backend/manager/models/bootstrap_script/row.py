from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.expression import false

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin


class BootstrapScriptRow(LifecycleTimestampsMixin, Base):
    """A bootstrap script set on an entity; at most one per entity is the default."""

    __tablename__ = "bootstrap_scripts"
    __table_args__ = (
        sa.Index(
            "uq_bootstrap_scripts_is_default",
            "entity_type",
            "entity_id",
            unique=True,
            postgresql_where=sa.text("is_default"),
        ),
        sa.CheckConstraint(f"char_length(script) <= {MAXIMUM_DOTFILE_SIZE}", name="script_length"),
    )

    id: Mapped[BootstrapScriptID] = mapped_column(
        "id",
        GUID(BootstrapScriptID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    entity_type: Mapped[EntityType] = mapped_column(sa.String(32), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    script: Mapped[BootstrapScript] = mapped_column(sa.Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=false())

    def to_data(self) -> BootstrapScriptData:
        return BootstrapScriptData(
            id=self.id,
            entity=RuntimeEntityID(self.entity_type, self.entity_id),
            script=BootstrapScript(self.script),
            is_default=self.is_default,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
