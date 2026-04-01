"""
Group (Project) DTOs for Manager API v2.
"""

from ai.backend.common.dto.manager.v2.group.request import (
    AdminSearchGroupsInput,
    AssignUsersToProjectInput,
    CreateGroupInput,
    DeleteGroupInput,
    GroupFilter,
    GroupOrder,
    PurgeGroupInput,
    SearchGroupsRequest,
    UnassignUsersFromProjectInput,
    UpdateGroupInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    AdminSearchGroupsPayload,
    AssignUsersToProjectPayload,
    DeleteProjectPayload,
    ProjectBasicInfo,
    ProjectLifecycleInfo,
    ProjectNode,
    ProjectOrganizationInfo,
    ProjectPayload,
    ProjectStorageInfo,
    PurgeProjectPayload,
    SearchProjectsPayload,
    UnassignUserError,
    UnassignUsersFromProjectPayload,
    VFolderHostPermissionEntry,
)
from ai.backend.common.dto.manager.v2.group.types import (
    DomainProjectScopeDTO,
    GroupDomainFilter,
    GroupOrderField,
    GroupUserFilter,
    OrderDirection,
    ProjectType,
    ProjectTypeFilter,
)

__all__ = (
    # Types
    "DomainProjectScopeDTO",
    "ProjectType",
    "OrderDirection",
    "GroupOrderField",
    "GroupDomainFilter",
    "GroupUserFilter",
    "ProjectTypeFilter",
    # Request DTOs
    "AdminSearchGroupsInput",
    "AssignUsersToProjectInput",
    "CreateGroupInput",
    "UpdateGroupInput",
    "DeleteGroupInput",
    "PurgeGroupInput",
    "GroupFilter",
    "GroupOrder",
    "SearchGroupsRequest",
    "UnassignUsersFromProjectInput",
    # Response DTOs
    "AdminSearchGroupsPayload",
    "AssignUsersToProjectPayload",
    "ProjectBasicInfo",
    "ProjectOrganizationInfo",
    "VFolderHostPermissionEntry",
    "ProjectStorageInfo",
    "ProjectLifecycleInfo",
    "ProjectNode",
    "ProjectPayload",
    "SearchProjectsPayload",
    "DeleteProjectPayload",
    "PurgeProjectPayload",
    "UnassignUserError",
    "UnassignUsersFromProjectPayload",
)
