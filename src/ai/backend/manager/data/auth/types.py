import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
    username: Optional[str]
    email: str
    password: Optional[str]
    need_password_change: bool
    full_name: Optional[str]
    description: Optional[str]
    is_active: bool
    status: UserStatus
    status_info: Optional[str]
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    password_changed_at: Optional[datetime]
    domain_name: str
    role: UserRole
    integration_id: Optional[str]
    resource_policy: str
    sudo_session_enabled: bool


@dataclass
class GroupMembershipData:
    group_id: uuid.UUID
    user_id: uuid.UUID
