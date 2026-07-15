"""Shared types used across all v2 DTO domains."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from functools import cached_property

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel

__all__ = (
    "BinarySizeInfo",
    "BinarySizeInput",
    "EnvironmentVariableEntryInfo",
    "EnvironmentVariableEntryInput",
    "EnvironmentVariablesInfo",
    "EnvironmentVariablesInput",
    "OrderDirection",
    "ResourceLimitEntryInfo",
    "ResourceSlotEntryInfo",
    "ResourceSlotEntryInput",
    "ResourceSlotInfo",
    "VFolderHostPermissionEntryInfo",
    "VFolderHostPermissionEntryInput",
)


class BinarySizeInput(BaseRequestModel):
    """Binary size input accepting bytes integer or human-readable string.

    Examples: '536870912', '512m', '1g', '2048k'
    """

    model_config = {"frozen": True}

    expr: str = Field(
        description="Size as bytes integer or human-readable format (e.g., '536870912', '512m', '1g').",
    )

    @cached_property
    def bytes(self) -> int:
        """Parse the expression to bytes integer."""
        from ai.backend.common.types import BinarySize

        return int(BinarySize.finite_from_str(self.expr))


class BinarySizeInfo(BaseResponseModel):
    """Binary size output with both the exact byte count and a human-readable form.

    ``expr`` mirrors the ``expr`` input field: an exact decimal byte-count string
    (e.g. '1073741824') that can be fed back into any ``BinarySizeInput``. It is a
    string so sizes beyond the GraphQL ``Int`` range (2 GiB) serialize correctly.
    """

    expr: str = Field(
        description="Exact size in bytes as a decimal string (e.g., '1073741824'); accepted as BinarySizeInput.expr.",
    )
    display: str = Field(description="Size in human-readable format (e.g., '1g', '512m').")


class OrderDirection(StrEnum):
    """Order direction for sorting. Shared across all v2 DTO domains."""

    ASC = "ASC"
    DESC = "DESC"


class ResourceSlotEntryInput(BaseRequestModel):
    """Single resource slot entry with resource type and quantity.

    Shared across all domains that accept resource allocations (session, deployment, etc.).
    """

    resource_type: str = Field(description="Resource type identifier (e.g., 'cpu', 'mem').")
    quantity: str = Field(description="Quantity of the resource as a decimal string.")


class ResourceSlotEntryInfo(BaseResponseModel):
    """A single resource slot entry with resource type and quantity."""

    resource_type: str = Field(description="Resource type identifier (e.g., cpu, mem, cuda.shares)")
    quantity: Decimal = Field(description="Quantity of the resource")


class ResourceLimitEntryInfo(BaseResponseModel):
    """A single resource limit entry that may be unlimited.

    When unlimited=True, quantity is null (no limit for this resource type).
    When unlimited=False, quantity holds the finite limit value.
    """

    resource_type: str = Field(description="Resource type identifier (e.g., cpu, mem, cuda.shares)")
    quantity: Decimal | None = Field(
        default=None, description="Limit quantity. Null when unlimited."
    )
    unlimited: bool = Field(default=False, description="Whether this resource type has no limit.")


class ResourceSlotInfo(BaseResponseModel):
    """Collection of compute resource allocations."""

    entries: list[ResourceSlotEntryInfo] = Field(description="List of resource allocations")


class VFolderHostPermissionEntryInfo(BaseResponseModel):
    """A single vfolder host with its granted permissions."""

    host: str = Field(description="Virtual folder host name (e.g., 'default', 'nfs-vol1').")
    permissions: list[str] = Field(
        description="List of permission values (e.g., 'mount-in-session', 'upload-file')."
    )


class VFolderHostPermissionEntryInput(BaseRequestModel):
    """A single vfolder host with its granted permissions (for create/update input)."""

    host: str = Field(description="Virtual folder host name (e.g., 'default', 'nfs-vol1').")
    permissions: list[str] = Field(
        description="List of permission values (e.g., 'mount-in-session', 'upload-file')."
    )


class EnvironmentVariableEntryInput(BaseRequestModel):
    """A single environment variable entry with key and value.

    Shared across all domains that accept environment variable lists (session, deployment, etc.).
    """

    key: str = Field(description="Environment variable key.")
    value: str = Field(description="Environment variable value.")


class EnvironmentVariablesInput(BaseRequestModel):
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryInput] = Field(
        description="List of environment variable entries."
    )


class EnvironmentVariableEntryInfo(BaseResponseModel):
    """A single environment variable entry with key and value."""

    key: str = Field(description="Environment variable key.")
    value: str = Field(description="Environment variable value.")


class EnvironmentVariablesInfo(BaseResponseModel):
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryInfo] = Field(
        description="List of environment variable entries."
    )
