"""
Common DTOs for group/project management used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    AddGroupMembersRequest,
    CreateGroupRequest,
    GroupFilter,
    ListGroupMembersRequest,
    RegistryQuotaModifyRequest,
    RegistryQuotaRequest,
    RemoveGroupMembersRequest,
    SearchGroupsRequest,
    UpdateGroupRequest,
)
from .response import (
    AddGroupMembersResponse,
    CreateGroupResponse,
    DeleteGroupResponse,
    GetGroupResponse,
    GroupDTO,
    GroupMemberDTO,
    ListGroupMembersResponse,
    PaginationInfo,
    PurgeGroupResponse,
    ReadRegistryQuotaResponse,
    RemoveGroupMembersResponse,
    SearchGroupsResponse,
    UpdateGroupResponse,
)
from .types import (
    GroupOrder,
    GroupOrderField,
)

__all__ = (
    # Types
    "GroupOrderField",
    "GroupOrder",
    # Request DTOs - Filters
    "GroupFilter",
    # Request DTOs - Search/List
    "SearchGroupsRequest",
    # Request DTOs - Create/Update
    "CreateGroupRequest",
    "UpdateGroupRequest",
    # Request DTOs - Member management
    "AddGroupMembersRequest",
    "RemoveGroupMembersRequest",
    "ListGroupMembersRequest",
    # Request DTOs - Registry quota
    "RegistryQuotaRequest",
    "RegistryQuotaModifyRequest",
    # Response DTOs - Data
    "GroupDTO",
    "GroupMemberDTO",
    # Response DTOs - CRUD
    "CreateGroupResponse",
    "GetGroupResponse",
    "SearchGroupsResponse",
    "UpdateGroupResponse",
    "DeleteGroupResponse",
    "PurgeGroupResponse",
    # Response DTOs - Member management
    "AddGroupMembersResponse",
    "RemoveGroupMembersResponse",
    "ListGroupMembersResponse",
    # Response DTOs - Registry quota
    "ReadRegistryQuotaResponse",
    # Response DTOs - Pagination
    "PaginationInfo",
)
