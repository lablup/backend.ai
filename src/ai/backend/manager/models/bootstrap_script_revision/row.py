import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.bootstrap_script_revision import BootstrapScriptRevisionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class BootstrapScriptRevisionRow(CreatedAtMixin, Base):
    """One write of a bootstrap script's content; rows are only ever added."""

    __tablename__ = "bootstrap_script_revisions"
    __table_args__ = (
        sa.UniqueConstraint("script_id", "revision_number"),
        sa.CheckConstraint(f"char_length(script) <= {MAXIMUM_DOTFILE_SIZE}", name="script_length"),
    )

    id: Mapped[BootstrapScriptRevisionID] = mapped_column(
        "id",
        GUID(BootstrapScriptRevisionID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    script_id: Mapped[BootstrapScriptID] = mapped_column(
        "script_id",
        GUID(BootstrapScriptID),
        sa.ForeignKey("bootstrap_scripts.id", ondelete="CASCADE"),
        nullable=False,
    )
    revision_number: Mapped[int] = mapped_column("revision_number", sa.Integer, nullable=False)
    script: Mapped[BootstrapScript] = mapped_column("script", sa.Text, nullable=False)
    creator_id: Mapped[UserID | None] = mapped_column(
        "creator_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )
