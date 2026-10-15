from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin


class DotfileRow(LifecycleTimestampsMixin, Base):
    """One dotfile; at most one variant per entity and path is the default."""

    __tablename__ = "dotfiles"
    __table_args__ = (
        sa.CheckConstraint("char_length(perm) <= 4", name="dotfile_perm_length"),
        sa.Index(
            "uq_dotfiles_is_default",
            "entity_type",
            "entity_id",
            "path",
            unique=True,
            postgresql_where=sa.text("is_default"),
        ),
        sa.CheckConstraint(
            f"octet_length(data) <= {MAXIMUM_DOTFILE_SIZE}", name="dotfile_data_length"
        ),
    )

    id: Mapped[DotfileID] = mapped_column(
        GUID(DotfileID), primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    entity_type: Mapped[EntityType] = mapped_column(sa.String(32), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    path: Mapped[str] = mapped_column(sa.Text, nullable=False)
    perm: Mapped[str] = mapped_column(sa.Text, nullable=False)
    data: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())

    def to_data(self) -> DotfileData:
        return DotfileData(
            id=self.id,
            entity=RuntimeEntityID(self.entity_type, self.entity_id),
            path=self.path,
            perm=self.perm,
            data=self.data,
            is_default=self.is_default,
        )
