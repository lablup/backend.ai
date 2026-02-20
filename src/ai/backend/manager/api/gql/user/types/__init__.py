"""User GraphQL types package."""

from .enums import (
    UserRoleEnumGQL,
    UserStatusEnumGQL,
)
from .filters import (
    UserDomainNestedFilter,
    UserFilterGQL,
    UserOrderByGQL,
    UserOrderFieldGQL,
    UserProjectNestedFilter,
    UserRoleEnumFilterGQL,
    UserStatusEnumFilterGQL,
)
from .inputs import (
    BulkCreateUserInputGQL,
    BulkUpdateUserV2InputGQL,
    BulkUpdateUserV2ItemInputGQL,
    CreateUserInputGQL,
    DeleteUsersInputGQL,
    PurgeUserInputGQL,
    PurgeUsersInputGQL,
    UpdateUserV2InputGQL,
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
    BulkCreateUserErrorGQL,
    BulkCreateUsersPayloadGQL,
    BulkUpdateUsersV2PayloadGQL,
    BulkUpdateUserV2ErrorGQL,
    CreateUserPayloadGQL,
    DeleteUserPayloadGQL,
    DeleteUsersPayloadGQL,
    PurgeUserPayloadGQL,
    PurgeUsersPayloadGQL,
    UpdateUserPayloadGQL,
)
from .scopes import (
    DomainUserScopeGQL,
    ProjectUserScopeGQL,
)

__all__ = [
    # Enums
    "UserStatusEnumGQL",
    "UserRoleEnumGQL",
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
    "UserDomainNestedFilter",
    "UserProjectNestedFilter",
    "UserFilterGQL",
    "UserOrderFieldGQL",
    "UserOrderByGQL",
    "UserStatusEnumFilterGQL",
    "UserRoleEnumFilterGQL",
    # Scopes
    "DomainUserScopeGQL",
    "ProjectUserScopeGQL",
    # Inputs
    "CreateUserInputGQL",
    "BulkCreateUserInputGQL",
    "BulkUpdateUserV2ItemInputGQL",
    "BulkUpdateUserV2InputGQL",
    "UpdateUserV2InputGQL",
    "DeleteUsersInputGQL",
    "PurgeUserInputGQL",
    "PurgeUsersInputGQL",
    # Payloads
    "CreateUserPayloadGQL",
    "BulkCreateUserErrorGQL",
    "BulkCreateUsersPayloadGQL",
    "BulkUpdateUserV2ErrorGQL",
    "BulkUpdateUsersV2PayloadGQL",
    "UpdateUserPayloadGQL",
    "DeleteUserPayloadGQL",
    "DeleteUsersPayloadGQL",
    "PurgeUserPayloadGQL",
    "PurgeUsersPayloadGQL",
]
