"""
Group (Project) DTOs for Manager API v2.
"""

from ai.backend.common.dto.manager.v2.group.request import (
    AdminSearchProjectsInput,
    AssignUsersByUsernameToProjectInput,
    AssignUsersToProjectInput,
    CreateProjectInput,
    DeleteProjectInput,
    ProjectFilter,
    ProjectOrder,
    PurgeProjectInput,
    SearchProjectsRequest,
    UnassignUsersFromProjectInput,
    UpdateProjectInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    AdminSearchGroupsPayload,
    AssignUsersByUsernameToProjectPayload,
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
    OrderDirection,
    ProjectDomainFilter,
    ProjectOrderField,
    ProjectType,
    ProjectTypeFilter,
    ProjectUserFilter,
)

__all__ = (
    # Types
    "DomainProjectScopeDTO",
    "OrderDirection",
    "ProjectDomainFilter",
    "ProjectOrderField",
    "ProjectType",
    "ProjectTypeFilter",
    "ProjectUserFilter",
    # Request DTOs
    "AdminSearchProjectsInput",
    "AssignUsersByUsernameToProjectInput",
    "AssignUsersToProjectInput",
    "CreateProjectInput",
    "UpdateProjectInput",
    "DeleteProjectInput",
    "PurgeProjectInput",
    "ProjectFilter",
    "ProjectOrder",
    "SearchProjectsRequest",
    "UnassignUsersFromProjectInput",
    # Response DTOs
    "AdminSearchGroupsPayload",
    "AssignUsersByUsernameToProjectPayload",
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
