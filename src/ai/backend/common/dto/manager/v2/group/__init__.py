"""
Group (Project) DTOs for Manager API v2.
"""

from ai.backend.common.dto.manager.v2.group.request import (
    CreateGroupInput,
    DeleteGroupInput,
    GroupFilter,
    GroupOrder,
    PurgeGroupInput,
    SearchGroupsRequest,
    UpdateGroupInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
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
    GroupOrderField,
    OrderDirection,
    ProjectType,
)

__all__ = (
    # Types
    "ProjectType",
    "OrderDirection",
    "GroupOrderField",
    # Request DTOs
    "CreateGroupInput",
    "UpdateGroupInput",
    "DeleteGroupInput",
    "PurgeGroupInput",
    "GroupFilter",
    "GroupOrder",
    "SearchGroupsRequest",
    # Response DTOs
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
