import enum
import uuid
from dataclasses import dataclass
from typing import Self

from sqlalchemy.engine.row import Row

from .enums import (
    EntityType,
    OperationType,
    RoleSource,
)
from .types import (
    ROLE_NAME_PREFIX,
    RoleCreateInput,
)

ENTITY_TYPES_IN_ROLE: set[EntityType] = {EntityType.USER}
OPERATIONS_IN_ROLE: set[OperationType] = {
    OperationType.READ,
    OperationType.UPDATE,
    OperationType.SOFT_DELETE,
    OperationType.HARD_DELETE,
    OperationType.GRANT_ALL,
    OperationType.GRANT_READ,
    OperationType.GRANT_UPDATE,
}


class UserRole(enum.StrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


@dataclass
class UserData:
    id: uuid.UUID
    username: str
    domain: str
    role: UserRole

    def role_name(self) -> str:
        return f"{ROLE_NAME_PREFIX}user_{self.username}"

    @classmethod
    def from_row(cls, user_row: Row) -> Self:
        return cls(
            id=user_row.uuid,
            username=user_row.username,
            domain=user_row.domain_name,
            role=user_row.role,
        )


def get_user_self_role_creation_input(user: UserData) -> RoleCreateInput:
    """
    Create a self role and permissions for a user.
    This role allows the user to manage their own data.
    """
    role_input = RoleCreateInput(
        name=user.role_name(),
        source=RoleSource.SYSTEM,
    )
    return role_input
