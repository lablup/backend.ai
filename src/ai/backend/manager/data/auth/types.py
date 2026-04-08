import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.models.user import UserRole, UserStatus


@dataclass
class SSHKeypair:
    ssh_public_key: str
    ssh_private_key: str


@dataclass
class AuthorizationResult:
    user_id: uuid.UUID
    access_key: str
    secret_key: str
    role: str
    status: str
    session_token: str


@dataclass
class UserData:
    uuid: uuid.UUID
    username: str | None
    email: str
    password: str | None
    need_password_change: bool
    full_name: str | None
    description: str | None
    is_active: bool
    status: UserStatus
    status_info: str | None
    created_at: datetime | None
    modified_at: datetime | None
    password_changed_at: datetime | None
    domain_name: str
    role: UserRole
    integration_name: str | None
    resource_policy: str
    sudo_session_enabled: bool

    def scope_id(self) -> ScopeId:
        return ScopeId(
            scope_type=ScopeType.USER,
            scope_id=str(self.uuid),
        )

    def role_name(self) -> str:
        return f"user-{str(self.uuid)[:8]}"

    def entity_operations(self) -> Mapping[RBACElementType, Iterable[OperationType]]:
        resource_entity_permissions = {
            entity.to_element(): OperationType.owner_operations()
            for entity in EntityType.owner_accessible_entity_types_in_user()
        }
        user_permissions = OperationType.owner_operations() - {OperationType.CREATE}
        return {RBACElementType.USER: user_permissions, **resource_entity_permissions}


@dataclass
class GroupMembershipData:
    group_id: uuid.UUID
    user_id: uuid.UUID
