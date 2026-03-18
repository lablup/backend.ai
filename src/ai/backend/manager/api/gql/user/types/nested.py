"""User GraphQL nested types for structured field groups."""

from __future__ import annotations

import strawberry

from ai.backend.common.dto.manager.v2.user.response import (
    EntityTimestamps as EntityTimestampsDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserBasicInfo as UserBasicInfoDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserContainerSettings as UserContainerSettingsDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserOrganizationInfo as UserOrganizationInfoDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserSecurityInfo as UserSecurityInfoDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserStatusInfo as UserStatusInfoDTO,
)

from .enums import UserRoleEnumGQL, UserStatusEnumGQL


@strawberry.experimental.pydantic.type(
    model=UserBasicInfoDTO,
    name="UserV2BasicInfo",
    description=(
        "Added in 26.2.0. Basic user profile information. "
        "Contains identity and descriptive fields for the user account."
    ),
    all_fields=True,
)
class UserBasicInfoGQL:
    """Basic user profile information."""


@strawberry.experimental.pydantic.type(
    model=UserStatusInfoDTO,
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


@strawberry.experimental.pydantic.type(
    model=UserOrganizationInfoDTO,
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


@strawberry.experimental.pydantic.type(
    model=UserSecurityInfoDTO,
    name="UserV2SecurityInfo",
    description=(
        "Added in 26.2.0. User security settings and authentication configuration. "
        "Contains IP restrictions, TOTP settings, and privilege flags."
    ),
    all_fields=True,
)
class UserSecurityInfoGQL:
    """User security settings and authentication configuration."""


@strawberry.experimental.pydantic.type(
    model=UserContainerSettingsDTO,
    name="UserV2ContainerSettings",
    description=(
        "Added in 26.2.0. Container execution settings for the user. "
        "Defines UID/GID mappings for containers created by this user."
    ),
    all_fields=True,
)
class UserContainerSettingsGQL:
    """Container execution settings for the user."""


@strawberry.experimental.pydantic.type(
    model=EntityTimestampsDTO,
    name="EntityTimestamps",
    description=(
        "Added in 26.2.0. Common timestamp fields for entity lifecycle tracking. "
        "Reusable across different entity types."
    ),
    all_fields=True,
)
class EntityTimestampsGQL:
    """Common timestamp fields for entity lifecycle tracking."""
