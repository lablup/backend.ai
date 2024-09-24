import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ..types import UserRole, UserStatus
from ..utils import verify_password
from .base import GUID, Base, IDColumn, PasswordColumn, StrEnumType

__all__: tuple[str, ...] = ("UserProfileRow",)


class UserProfileRow(Base):
    __tablename__ = "user_profiles"
    id = IDColumn()
    user_id = sa.Column("user_id", GUID, nullable=False)
    username = sa.Column("username", sa.String(length=64), index=True, nullable=False, unique=True)
    email = sa.Column("email", sa.String(length=64), index=True, nullable=False)
    password = sa.Column("password", PasswordColumn(), nullable=False)
    need_password_change = sa.Column("need_password_change", sa.Boolean, server_default=sa.false())
    password_changed_at = sa.Column(
        "password_changed_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
    )
    full_name = sa.Column("full_name", sa.String(length=64))
    description = sa.Column("description", sa.String(length=500))

    role = sa.Column(
        "role",
        StrEnumType(UserRole),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
        nullable=False,
    )
    status = sa.Column(
        "status", StrEnumType(UserStatus), server_default=UserStatus.ACTIVE.value, nullable=False
    )
    status_info = sa.Column("status_info", sa.Unicode(), nullable=True)

    created_at = sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    modified_at = sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    )

    user_row = relationship(
        "UserRow",
        back_populates="user_profile_rows",
        primaryjoin="UserRow.uuid == foreign(UserProfileRow.user_id)",
    )


def compare_to_hashed_password(raw_password: str, hashed_password: str) -> bool:
    """
    Compare a raw string password value to hased password.
    """
    return verify_password(raw_password, hashed_password)
