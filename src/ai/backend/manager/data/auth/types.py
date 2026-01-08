from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.data.user.types import UserData as FullUserData
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


@dataclass
class CredentialData:
    """
    Aggregated credential data for authentication.

    Combines user, keypair, and their resource policies into a single data structure.
    Used by authentication middleware to populate request context.
    """

    user: FullUserData
    user_resource_policy: UserResourcePolicyData
    keypair: KeyPairData
    keypair_resource_policy: KeyPairResourcePolicyData

    @property
    def is_admin(self) -> bool:
        """Check if the keypair has admin privileges."""
        return self.keypair.is_admin

    @property
    def is_superadmin(self) -> bool:
        """Check if the user has superadmin role."""
        return self.user.role == UserRole.SUPERADMIN
