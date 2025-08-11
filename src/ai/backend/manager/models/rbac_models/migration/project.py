import uuid
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

ADMIN_ACCESSIBLE_ENTITY_TYPES_IN_PROJECT = {
    EntityType.USER,
}
MEMBER_ACCESSIBLE_ENTITY_TYPES_IN_PROJECT = {
    EntityType.USER,
}


@dataclass
class ProjectData:
    id: uuid.UUID

    def role_name(self, is_admin: bool) -> str:
        """
        Generate a role name for a project.

        'role_project_<project_id>_admin' for admin roles.
        'role_project_<project_id>_member' for member roles.
        """
        role_type = ADMIN_ROLE_NAME_SUFFIX if is_admin else "_member"
        return f"{ROLE_NAME_PREFIX}project_{str(self.id)[:8]}{role_type}"

    @classmethod
    def from_row(cls, group_row: Row) -> Self:
        return cls(id=group_row.id)


def get_project_admin_role_creation_input(project: ProjectData) -> RoleCreateInput:
    """
    Create an admin role for a project.
    This role allows the user to manage the project.
    """
    return RoleCreateInput(
        name=project.role_name(is_admin=True),
        source=RoleSource.SYSTEM,
    )


def get_project_member_role_creation_input(project: ProjectData) -> RoleCreateInput:
    """
    Create a member role for a project.
    This role allows the user to read the project.
    """
    return RoleCreateInput(
        name=project.role_name(is_admin=False),
        source=RoleSource.CUSTOM,
    )
