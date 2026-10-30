import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.dotfile_revision import DotfileRevisionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class DotfileRevisionRow(CreatedAtMixin, Base):
    """One write of a dotfile's permission and content; rows are only ever added."""

    __tablename__ = "dotfile_revisions"
    __table_args__ = (
        sa.UniqueConstraint("dotfile_id", "revision_number"),
        sa.CheckConstraint("char_length(perm) <= 4", name="perm_length"),
        sa.CheckConstraint(f"char_length(data) <= {MAXIMUM_DOTFILE_SIZE}", name="data_length"),
    )

    id: Mapped[DotfileRevisionID] = mapped_column(
        "id",
        GUID(DotfileRevisionID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    dotfile_id: Mapped[DotfileID] = mapped_column(
        "dotfile_id",
        GUID(DotfileID),
        sa.ForeignKey("dotfiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    revision_number: Mapped[int] = mapped_column("revision_number", sa.Integer, nullable=False)
    perm: Mapped[str] = mapped_column("perm", sa.Text, nullable=False)
    data: Mapped[str] = mapped_column("data", sa.Text, nullable=False)
    creator_id: Mapped[UserID | None] = mapped_column(
        "creator_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )
