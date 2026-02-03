import uuid
from dataclasses import dataclass
from datetime import datetime

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
    integration_id: str | None
    resource_policy: str
    sudo_session_enabled: bool


@dataclass
class GroupMembershipData:
    group_id: uuid.UUID
    user_id: uuid.UUID
