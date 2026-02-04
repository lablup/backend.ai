"""User V2 GraphQL types package."""

from .enums import (
    UserRoleEnum,
    UserStatusEnum,
)
from .filters import (
    UserRoleEnumFilter,
    UserStatusEnumFilter,
    UserV2Filter,
    UserV2OrderBy,
    UserV2OrderField,
    UserV2Scope,
)
from .inputs import (
    BulkCreateUserV2Input,
    CreateUserV2Input,
    DeleteUsersV2Input,
    PurgeUsersV2Input,
    PurgeUserV2Input,
    UpdateUserV2Input,
)
from .nested import (
    EntityTimestampsGQL,
    UserBasicInfoGQL,
    UserContainerSettingsGQL,
    UserOrganizationInfoGQL,
    UserSecurityInfoGQL,
    UserStatusInfoGQL,
)
from .node import (
    UserV2Connection,
    UserV2Edge,
    UserV2GQL,
)
from .payloads import (
    BulkCreateUsersPayload,
    CreateUserV2Payload,
    DeleteUserPayload,
    DeleteUsersPayload,
    PurgeUserPayload,
    PurgeUsersPayload,
    UpdateUserV2Payload,
)
from .scopes import (
    DomainUserScope,
    ProjectUserScope,
)

__all__ = [
    # Enums
    "UserStatusEnum",
    "UserRoleEnum",
    # Nested Types
    "UserBasicInfoGQL",
    "UserStatusInfoGQL",
    "UserOrganizationInfoGQL",
    "UserSecurityInfoGQL",
    "UserContainerSettingsGQL",
    "EntityTimestampsGQL",
    # Node Types
    "UserV2GQL",
    "UserV2Edge",
    "UserV2Connection",
    # Filters
    "UserV2Filter",
    "UserV2OrderField",
    "UserV2OrderBy",
    "UserV2Scope",
    "UserStatusEnumFilter",
    "UserRoleEnumFilter",
    # Scopes
    "DomainUserScope",
    "ProjectUserScope",
    # Inputs
    "CreateUserV2Input",
    "BulkCreateUserV2Input",
    "UpdateUserV2Input",
    "DeleteUsersV2Input",
    "PurgeUserV2Input",
    "PurgeUsersV2Input",
    # Payloads
    "CreateUserV2Payload",
    "BulkCreateUsersPayload",
    "UpdateUserV2Payload",
    "DeleteUserPayload",
    "DeleteUsersPayload",
    "PurgeUserPayload",
    "PurgeUsersPayload",
]
