"""Shared GQL types used across multiple entity domains.

Types defined here are reusable building blocks (resource slots, vfolder permissions, etc.)
that do not belong to any specific entity domain.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInfo,
    BinarySizeInput,
    ResourceLimitEntryInfo,
    ResourceSlotEntryInfo,
    ResourceSlotEntryInput,
    ResourceSlotInfo,
    VFolderHostPermissionEntryInfo,
    VFolderHostPermissionEntryInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Binary size input accepting bytes integer or human-readable string.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="BinarySizeInput",
)
class BinarySizeInputGQL(PydanticInputMixin[BinarySizeInput]):
    """Binary size input (e.g., '536870912', '512m', '1g')."""

    expr: str = gql_field(
        description="Size as bytes integer or human-readable format (e.g., '536870912', '512m', '1g').",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Binary size with both raw bytes and human-readable format.",
    ),
    model=BinarySizeInfo,
    all_fields=True,
    name="BinarySizeInfo",
)
class BinarySizeInfoGQL(PydanticOutputMixin[BinarySizeInfo]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A resource limit entry that may be unlimited.",
    ),
    model=ResourceLimitEntryInfo,
    all_fields=True,
    name="ResourceLimitEntry",
)
class ResourceLimitEntryGQL(PydanticOutputMixin[ResourceLimitEntryInfo]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A single entry representing one resource type and its allocated quantity. "
            "Resource types include compute resources (cpu, mem), accelerators (cuda.shares, cuda.device, "
            "rocm.device), and custom resources defined by plugins."
        ),
    ),
    model=ResourceSlotEntryInfo,
    name="ResourceSlotEntry",
)
class ResourceSlotEntryGQL(PydanticOutputMixin[ResourceSlotEntryInfo]):
    """Single resource slot entry with resource type and quantity."""

    resource_type: str = gql_field(
        description="Resource type identifier. Common types include: 'cpu' (CPU cores), 'mem' (memory in bytes), 'cuda.shares' (fractional GPU), 'cuda.device' (whole GPU devices), 'rocm.device' (AMD GPU devices). Custom accelerator plugins may define additional types."
    )
    quantity: Decimal = gql_field(
        description="Quantity of the resource. For 'cpu': number of cores (e.g., 2.0, 0.5). For 'mem': bytes (e.g., 4294967296 for 4GB). For accelerators: device count or share fraction."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A collection of compute resource allocations. "
            "Represents the resources consumed, allocated, or available for a workload. "
            "Each entry specifies a resource type and its quantity."
        ),
    ),
    model=ResourceSlotInfo,
    name="ResourceSlot",
)
class ResourceSlotGQL(PydanticOutputMixin[ResourceSlotInfo]):
    """Resource slot containing multiple resource type entries."""

    entries: list[ResourceSlotEntryGQL] = gql_field(
        description="List of resource allocations. Each entry contains a resource type and quantity pair."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A single entry representing one resource type and its allocated quantity.",
        added_version="26.1.0",
    ),
    name="ResourceSlotEntryInput",
)
class ResourceSlotEntryInputGQL(PydanticInputMixin[ResourceSlotEntryInput]):
    """Single resource slot entry input with resource type and quantity."""

    resource_type: str = gql_field(
        description="Resource type identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    quantity: str = gql_field(description="Quantity of the resource as a decimal string.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for a vfolder host with its permissions.",
    ),
    name="VFolderHostPermissionEntryInput",
)
class VFolderHostPermissionEntryInputGQL(PydanticInputMixin[VFolderHostPermissionEntryInput]):
    """Input for a vfolder host permission entry."""

    host: str = gql_field(description="Virtual folder host name.")
    permissions: list[str] = gql_field(description="List of permission values.")


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Atomic permissions for virtual folders on a storage host.",
    ),
    name="VFolderHostPermissionV2",
)
class VFolderHostPermissionEnum(StrEnum):
    """Virtual folder host permission enum."""

    CREATE_VFOLDER = "create-vfolder"
    MODIFY_VFOLDER = "modify-vfolder"
    DELETE_VFOLDER = "delete-vfolder"
    MOUNT_IN_SESSION = "mount-in-session"
    UPLOAD_FILE = "upload-file"
    DOWNLOAD_FILE = "download-file"
    INVITE_OTHERS = "invite-others"
    SET_USER_PERM = "set-user-specific-permission"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Storage host permission configuration. "
            "Defines what operations are allowed for a specific storage host."
        ),
    ),
    model=VFolderHostPermissionEntryInfo,
    name="VFolderHostPermissionEntry",
)
class VFolderHostPermissionEntryGQL(PydanticOutputMixin[VFolderHostPermissionEntryInfo]):
    """Storage host permission entry."""

    host: str = gql_field(description="Storage host identifier (e.g., 'default', 'storage-01').")
    permissions: list[VFolderHostPermissionEnum] = gql_field(
        description="List of permissions granted for this host."
    )
