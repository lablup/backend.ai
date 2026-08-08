import sqlalchemy as sa
from sqlalchemy.orm import relationship

from .base import GUID, Base, IDColumn

__all__: tuple[str, ...] = (
    "ApplicationRow",
    "AssociationApplicationUserRow",
)


class ApplicationRow(Base):
    __tablename__ = "applications"
    id = IDColumn()
    name = sa.Column("name", sa.String(length=64), unique=True, nullable=False)
    redirect_to = sa.Column("redirect_to", sa.Text, nullable=True)
    token_secret = sa.Column("token_secret", sa.Text, nullable=False)

    user_assoc_rows = relationship(
        "AssociationApplicationUserRow",
        back_populates="application_row",
        primaryjoin="ApplicationRow.id == foreign(AssociationApplicationUserRow.application_id)",
    )


class AssociationApplicationUserRow(Base):
    __tablename__ = "association_applications_users"
    __table_args__ = (
        sa.Index(
            "ix_user_id_application_id",
            "user_id",
            "application_id",
            unique=True,
        ),
    )

    id = IDColumn()
    user_id = sa.Column("user_id", GUID, nullable=False)
    application_id = sa.Column("application_id", GUID, nullable=False)

    application_row = relationship(
        "ApplicationRow",
        back_populates="user_assoc_rows",
        primaryjoin="ApplicationRow.id == foreign(AssociationApplicationUserRow.application_id)",
    )
    user_row = relationship(
        "UserRow",
        back_populates="app_assoc_rows",
        primaryjoin="UserRow.uuid == foreign(AssociationApplicationUserRow.user_id)",
    )
