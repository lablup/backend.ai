from dataclasses import dataclass
from typing import Self

from sqlalchemy.engine.row import Row

from .enums import (
    EntityType,
    RoleSource,
)
from .types import (
    ADMIN_ROLE_NAME_SUFFIX,
    ROLE_NAME_PREFIX,
    RoleCreateInput,
)

ADMIN_ACCESSIBLE_ENTITY_TYPES: set[EntityType] = {
    EntityType.USER,
}
MEMBER_ACCESSIBLE_ENTITY_TYPES: set[EntityType] = set()


@dataclass
class DomainData:
    name: str

    def role_name(self, is_admin: bool) -> str:
        """
        Generate a role name for a domain.

        'role_domain_<domain_name>_admin' for admin roles.
        'role_domain_<domain_name>_member' for member roles.
        """
        role_type = ADMIN_ROLE_NAME_SUFFIX if is_admin else "_member"
        return f"{ROLE_NAME_PREFIX}domain_{self.name}{role_type}"

    @classmethod
    def from_row(cls, domain_row: Row) -> Self:
        return cls(name=domain_row.name)


def get_domain_admin_role_creation_input(domain: DomainData) -> RoleCreateInput:
    """
    Create an admin role for a domain.
    This role allows the user to manage the domain.
    """
    return RoleCreateInput(
        name=domain.role_name(is_admin=True),
        source=RoleSource.SYSTEM,
    )


def get_domain_member_role_creation_input(domain: DomainData) -> RoleCreateInput:
    """
    Create an admin role for a domain.
    This role allows the user to manage the domain.
    """
    return RoleCreateInput(
        name=domain.role_name(is_admin=False),
        source=RoleSource.CUSTOM,
    )
