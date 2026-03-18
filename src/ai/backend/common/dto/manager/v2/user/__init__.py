"""
User DTO v2 models for Manager API.
"""

from ai.backend.common.dto.manager.v2.user.request import (
    BulkCreateUsersInput,
    BulkPurgeUsersInput,
    BulkPurgeUsersOptions,
    BulkUpdateUserItemInput,
    BulkUpdateUsersInput,
    CreateUserInput,
    DeleteUserInput,
    DeleteUsersInput,
    PurgeUserInput,
    PurgeUserV2Input,
    SearchUsersRequest,
    UpdateMyAllowedClientIPInput,
    UpdateUserInput,
    UserFilter,
    UserOrder,
)
from ai.backend.common.dto.manager.v2.user.response import (
    DeleteUserPayload,
    EntityTimestamps,
    PurgeUserPayload,
    SearchUsersPayload,
    UserBasicInfo,
    UserContainerSettings,
    UserNode,
    UserOrganizationInfo,
    UserPayload,
    UserSecurityInfo,
    UserStatusInfo,
)
from ai.backend.common.dto.manager.v2.user.types import (
    OrderDirection,
    UserOrderField,
    UserRole,
    UserStatus,
)

__all__ = (
    # Request DTOs
    "BulkCreateUsersInput",
    "BulkPurgeUsersInput",
    "BulkPurgeUsersOptions",
    "BulkUpdateUserItemInput",
    "BulkUpdateUsersInput",
    "CreateUserInput",
    "UpdateUserInput",
    "DeleteUserInput",
    "DeleteUsersInput",
    "PurgeUserInput",
    "PurgeUserV2Input",
    "UpdateMyAllowedClientIPInput",
    "UserFilter",
    "UserOrder",
    "SearchUsersRequest",
    # Response DTOs
    "UserBasicInfo",
    "UserStatusInfo",
    "UserOrganizationInfo",
    "UserSecurityInfo",
    "UserContainerSettings",
    "EntityTimestamps",
    "UserNode",
    "UserPayload",
    "SearchUsersPayload",
    "DeleteUserPayload",
    "PurgeUserPayload",
    # Types
    "UserStatus",
    "UserRole",
    "OrderDirection",
    "UserOrderField",
)
