from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TypedDict

from ai.backend.common.types import (
    DefaultForUnspecified,
    ReadableCIDR,
    ResourceSlot,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.user.types import UserRole, UserStatus

# TypedDict definitions for legacy request dict format compatibility


class KeypairResourcePolicyDict(TypedDict):
    """Legacy format for request['keypair']['resource_policy']."""

    name: str
    created_at: datetime | None
    default_for_unspecified: DefaultForUnspecified
    total_resource_slots: ResourceSlot
    max_session_lifetime: int
    max_concurrent_sessions: int
    max_pending_session_count: int | None
    max_pending_session_resource_slots: ResourceSlot | None
    max_concurrent_sftp_sessions: int
    max_containers_per_session: int
    idle_timeout: int
    allowed_vfolder_hosts: VFolderHostPermissionMap


class KeypairDict(TypedDict):
    """Legacy format for request['keypair']."""

    user_id: str | None
    access_key: str
    # Note: secret_key is intentionally excluded for security
    is_active: bool | None
    is_admin: bool | None
    created_at: datetime | None
    modified_at: datetime | None
    last_used: datetime | None
    rate_limit: int | None
    num_queries: int | None
    ssh_public_key: str | None
    ssh_private_key: str | None
    user: uuid.UUID
    resource_policy: KeypairResourcePolicyDict
    dotfiles: bytes
    bootstrap_script: str


class UserResourcePolicyDict(TypedDict):
    """Legacy format for request['user']['resource_policy']."""

    name: str
    created_at: datetime | None
    max_vfolder_count: int
    max_quota_scope_size: int
    max_session_count_per_model_session: int
    max_customized_image_count: int


class UserDict(TypedDict):
    """Legacy format for request['user']."""

    uuid: uuid.UUID
    id: uuid.UUID  # Same as keypair.user for compatibility
    username: str | None
    email: str
    need_password_change: bool | None
    password_changed_at: datetime | None
    full_name: str | None
    status: UserStatus
    status_info: str | None
    modified_at: datetime | None
    domain_name: str | None
    role: UserRole | None
    allowed_client_ip: list[ReadableCIDR] | None
    totp_key: str | None
    totp_activated: bool | None
    totp_activated_at: datetime | None
    resource_policy: UserResourcePolicyDict
    sudo_session_enabled: bool
    main_access_key: str | None
    integration_id: str | None
    container_uid: int | None
    container_main_gid: int | None
    container_gids: list[int] | None


# Pure dataclass definitions for CredentialData (no ORM dependencies)


@dataclass
class KeypairResourcePolicyDataForCredential:
    """Keypair resource policy data without ORM dependencies."""

    name: str
    created_at: datetime | None
    default_for_unspecified: DefaultForUnspecified
    total_resource_slots: ResourceSlot
    max_session_lifetime: int
    max_concurrent_sessions: int
    max_pending_session_count: int | None
    max_pending_session_resource_slots: ResourceSlot | None
    max_concurrent_sftp_sessions: int
    max_containers_per_session: int
    idle_timeout: int
    allowed_vfolder_hosts: VFolderHostPermissionMap

    def to_dict(self) -> KeypairResourcePolicyDict:
        return KeypairResourcePolicyDict(
            name=self.name,
            created_at=self.created_at,
            default_for_unspecified=self.default_for_unspecified,
            total_resource_slots=self.total_resource_slots,
            max_session_lifetime=self.max_session_lifetime,
            max_concurrent_sessions=self.max_concurrent_sessions,
            max_pending_session_count=self.max_pending_session_count,
            max_pending_session_resource_slots=self.max_pending_session_resource_slots,
            max_concurrent_sftp_sessions=self.max_concurrent_sftp_sessions,
            max_containers_per_session=self.max_containers_per_session,
            idle_timeout=self.idle_timeout,
            allowed_vfolder_hosts=self.allowed_vfolder_hosts,
        )


@dataclass
class UserResourcePolicyDataForCredential:
    """User resource policy data without ORM dependencies."""

    name: str
    created_at: datetime | None
    max_vfolder_count: int
    max_quota_scope_size: int
    max_session_count_per_model_session: int
    max_customized_image_count: int

    def to_dict(self) -> UserResourcePolicyDict:
        return UserResourcePolicyDict(
            name=self.name,
            created_at=self.created_at,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_session_count_per_model_session=self.max_session_count_per_model_session,
            max_customized_image_count=self.max_customized_image_count,
        )


@dataclass
class KeypairDataForCredential:
    """Keypair data for authentication without ORM dependencies."""

    user_id: str | None
    access_key: str
    secret_key: str
    is_active: bool
    is_admin: bool
    created_at: datetime | None
    modified_at: datetime | None
    last_used: datetime | None
    rate_limit: int | None
    num_queries: int | None
    ssh_public_key: str | None
    ssh_private_key: str | None
    user: uuid.UUID
    resource_policy_name: str
    dotfiles: bytes
    bootstrap_script: str
    resource_policy: KeypairResourcePolicyDataForCredential


@dataclass
class UserDataForCredential:
    """User data for authentication without ORM dependencies."""

    uuid: uuid.UUID
    username: str | None
    email: str
    need_password_change: bool | None
    password_changed_at: datetime | None
    full_name: str | None
    status: UserStatus
    status_info: str | None
    modified_at: datetime | None
    domain_name: str | None
    role: UserRole | None
    allowed_client_ip: list[ReadableCIDR] | None
    totp_key: str | None
    totp_activated: bool | None
    totp_activated_at: datetime | None
    resource_policy_name: str
    sudo_session_enabled: bool
    main_access_key: str | None
    integration_id: str | None
    container_uid: int | None
    container_main_gid: int | None
    container_gids: list[int] | None
    resource_policy: UserResourcePolicyDataForCredential


@dataclass
class CredentialData:
    """
    Aggregated credential data for authentication.

    Pure dataclass with no ORM dependencies.
    Used by authentication middleware to populate request context.
    """

    user: UserDataForCredential
    keypair: KeypairDataForCredential

    @property
    def secret_key(self) -> str:
        """Get secret key for signature validation."""
        return self.keypair.secret_key

    @property
    def is_admin(self) -> bool:
        """Check if the keypair has admin privileges."""
        return self.keypair.is_admin

    @property
    def is_superadmin(self) -> bool:
        """Check if the user has superadmin role."""
        return self.user.role == UserRole.SUPERADMIN

    def to_keypair_dict(self) -> KeypairDict:
        """
        Convert to legacy request["keypair"] dict format.

        Matches the exact output of the pre-migration code:
        - All keypairs columns except secret_key
        - Nested resource_policy dict with all keypair_resource_policies columns
        """
        return KeypairDict(
            user_id=self.keypair.user_id,
            access_key=self.keypair.access_key,
            is_active=self.keypair.is_active,
            is_admin=self.keypair.is_admin,
            created_at=self.keypair.created_at,
            modified_at=self.keypair.modified_at,
            last_used=self.keypair.last_used,
            rate_limit=self.keypair.rate_limit,
            num_queries=self.keypair.num_queries,
            ssh_public_key=self.keypair.ssh_public_key,
            ssh_private_key=self.keypair.ssh_private_key,
            user=self.keypair.user,
            resource_policy=self.keypair.resource_policy.to_dict(),
            dotfiles=self.keypair.dotfiles,
            bootstrap_script=self.keypair.bootstrap_script,
        )

    def to_user_dict(self) -> UserDict:
        """
        Convert to legacy request["user"] dict format.

        Excludes password, description, and created_at for security and compatibility.
        """
        return UserDict(
            uuid=self.user.uuid,
            id=self.keypair.user,  # Same as keypair.user for compatibility
            username=self.user.username,
            email=self.user.email,
            need_password_change=self.user.need_password_change,
            password_changed_at=self.user.password_changed_at,
            full_name=self.user.full_name,
            status=self.user.status,
            status_info=self.user.status_info,
            modified_at=self.user.modified_at,
            domain_name=self.user.domain_name,
            role=self.user.role,
            allowed_client_ip=self.user.allowed_client_ip,
            totp_key=self.user.totp_key,
            totp_activated=self.user.totp_activated,
            totp_activated_at=self.user.totp_activated_at,
            resource_policy=self.user.resource_policy.to_dict(),
            sudo_session_enabled=self.user.sudo_session_enabled,
            main_access_key=self.user.main_access_key,
            integration_id=self.user.integration_id,
            container_uid=self.user.container_uid,
            container_main_gid=self.user.container_main_gid,
            container_gids=self.user.container_gids,
        )


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
