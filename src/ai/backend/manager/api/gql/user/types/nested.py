"""User GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime

import strawberry

from .enums import UserRoleEnumGQL, UserStatusEnumGQL


@strawberry.type(
    name="UserV2BasicInfo",
    description=(
        "Added in 26.2.0. Basic user profile information. "
        "Contains identity and descriptive fields for the user account."
    ),
)
class UserBasicInfoGQL:
    """Basic user profile information."""

    username: str | None = strawberry.field(
        description="Unique username for login. May be null if only email-based login is used."
    )
    email: str = strawberry.field(
        description="User's email address. Used for login and notifications."
    )
    full_name: str | None = strawberry.field(description="User's full display name.")
    description: str | None = strawberry.field(
        description="Optional description or notes about the user."
    )


@strawberry.type(
    name="UserV2StatusInfo",
    description=(
        "Added in 26.2.0. User account status information. "
        "Contains current status and password-related flags."
    ),
)
class UserStatusInfoGQL:
    """User account status information."""

    status: UserStatusEnumGQL = strawberry.field(
        description=(
            "Current account status. See UserStatusV2 enum for possible values. "
            "Replaces the deprecated is_active field."
        )
    )
    status_info: str | None = strawberry.field(
        description="Additional information about the current status, such as reason for deactivation."
    )
    need_password_change: bool | None = strawberry.field(
        description="If true, user must change password on next login."
    )


@strawberry.type(
    name="UserV2OrganizationInfo",
    description=(
        "Added in 26.2.0. User's organizational context and permissions. "
        "Contains domain membership, role, and resource policy information."
    ),
)
class UserOrganizationInfoGQL:
    """User's organizational context and permissions."""

    domain_name: str | None = strawberry.field(
        description="Name of the domain this user belongs to."
    )
    role: UserRoleEnumGQL | None = strawberry.field(
        description="User's role determining access permissions. See UserRoleV2 enum."
    )
    resource_policy: str = strawberry.field(
        description="Name of the user resource policy applied to this user."
    )
    main_access_key: str | None = strawberry.field(
        description="Primary API access key for this user."
    )


@strawberry.type(
    name="UserV2SecurityInfo",
    description=(
        "Added in 26.2.0. User security settings and authentication configuration. "
        "Contains IP restrictions, TOTP settings, and privilege flags."
    ),
)
class UserSecurityInfoGQL:
    """User security settings and authentication configuration."""

    allowed_client_ip: list[str] | None = strawberry.field(
        description=(
            "List of allowed client IP addresses or CIDR ranges. "
            "If set, login is restricted to these IP addresses. "
            "Supports both IPv4 and IPv6 formats (e.g., '192.168.1.0/24', '::1')."
        )
    )
    totp_activated: bool | None = strawberry.field(
        description="Whether TOTP (Time-based One-Time Password) two-factor authentication is enabled."
    )
    totp_activated_at: datetime | None = strawberry.field(
        description="Timestamp when TOTP was activated."
    )
    sudo_session_enabled: bool = strawberry.field(
        description="Whether this user can create sudo (privileged) sessions."
    )


@strawberry.type(
    name="UserV2ContainerSettings",
    description=(
        "Added in 26.2.0. Container execution settings for the user. "
        "Defines UID/GID mappings for containers created by this user."
    ),
)
class UserContainerSettingsGQL:
    """Container execution settings for the user."""

    container_uid: int | None = strawberry.field(
        description="User ID (UID) to use inside containers. If null, system default is used."
    )
    container_main_gid: int | None = strawberry.field(
        description="Primary group ID (GID) to use inside containers. If null, system default is used."
    )
    container_gids: list[int] | None = strawberry.field(
        description="Additional supplementary group IDs for container processes."
    )


@strawberry.type(
    name="EntityTimestamps",
    description=(
        "Added in 26.2.0. Common timestamp fields for entity lifecycle tracking. "
        "Reusable across different entity types."
    ),
)
class EntityTimestampsGQL:
    """Common timestamp fields for entity lifecycle tracking."""

    created_at: datetime | None = strawberry.field(
        description="Timestamp when this entity was created."
    )
    modified_at: datetime | None = strawberry.field(
        description="Timestamp when this entity was last modified."
    )
