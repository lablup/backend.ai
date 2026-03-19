"""
Group (Project) DTOs for Manager API v2.
"""

from ai.backend.common.dto.manager.v2.group.request import (
    AdminSearchGroupsInput,
    CreateGroupInput,
    DeleteGroupInput,
    GroupFilter,
    GroupOrder,
    PurgeGroupInput,
    SearchGroupsRequest,
    UpdateGroupInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    AdminSearchGroupsPayload,
    DeleteProjectPayload,
    ProjectBasicInfo,
    ProjectLifecycleInfo,
    ProjectNode,
    ProjectOrganizationInfo,
    ProjectPayload,
    ProjectStorageInfo,
    PurgeProjectPayload,
    SearchProjectsPayload,
    VFolderHostPermissionEntry,
)
from ai.backend.common.dto.manager.v2.group.types import (
    GroupDomainFilter,
    GroupOrderField,
    GroupUserFilter,
    OrderDirection,
    ProjectType,
    ProjectTypeFilter,
)

__all__ = (
    # Types
    "ProjectType",
    "OrderDirection",
    "GroupOrderField",
    "GroupDomainFilter",
    "GroupUserFilter",
    "ProjectTypeFilter",
    # Request DTOs
    "AdminSearchGroupsInput",
    "CreateGroupInput",
    "UpdateGroupInput",
    "DeleteGroupInput",
    "PurgeGroupInput",
    "GroupFilter",
    "GroupOrder",
    "SearchGroupsRequest",
    # Response DTOs
    "AdminSearchGroupsPayload",
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
)
