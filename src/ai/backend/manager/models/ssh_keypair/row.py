import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin


class SSHKeypairRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "ssh_keypairs"
    __table_args__ = (
        sa.Index(
            "uq_ssh_keypairs_is_default",
            "user_id",
            unique=True,
            postgresql_where=sa.text("is_default"),
        ),
    )
    id: Mapped[SSHKeypairID] = mapped_column(
        GUID(SSHKeypairID), primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    user_id: Mapped[UserID] = mapped_column(
        GUID(UserID), sa.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False, index=True
    )
    public_key: Mapped[str] = mapped_column(sa.Text, nullable=False)
    private_key: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
