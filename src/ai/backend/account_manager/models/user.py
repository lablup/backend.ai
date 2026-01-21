from sqlalchemy.orm import relationship

from .base import Base, IDColumn

__all__: tuple[str, ...] = ("UserRow",)


class UserRow(Base):
    __tablename__ = "users"
    uuid = IDColumn("uuid")

    keypair_rows = relationship(
        "KeypairRow",
        back_populates="user_row",
        primaryjoin="UserRow.uuid == foreign(KeypairRow.user_id)",
    )
    user_profile_rows = relationship(
        "UserProfileRow",
        back_populates="user_row",
        primaryjoin="UserRow.uuid == foreign(UserProfileRow.user_id)",
    )
    app_assoc_rows = relationship(
        "AssociationApplicationUserRow",
        back_populates="user_row",
        primaryjoin="UserRow.uuid == foreign(AssociationApplicationUserRow.user_id)",
    )
