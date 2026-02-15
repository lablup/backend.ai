"""
Common DTOs for group/project management used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    AddGroupMembersRequest,
    CreateGroupRequest,
    GroupFilter,
    ListGroupMembersRequest,
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
    # Response DTOs - Data
    "GroupDTO",
    "GroupMemberDTO",
    # Response DTOs - CRUD
    "CreateGroupResponse",
    "GetGroupResponse",
    "SearchGroupsResponse",
    "UpdateGroupResponse",
    "DeleteGroupResponse",
    # Response DTOs - Member management
    "AddGroupMembersResponse",
    "RemoveGroupMembersResponse",
    "ListGroupMembersResponse",
    # Response DTOs - Pagination
    "PaginationInfo",
)
