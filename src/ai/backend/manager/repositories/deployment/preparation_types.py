"""Type definitions for deployment repository."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ai.backend.manager.models.vfolder import VFolderOwnershipType
from ai.backend.manager.services.model_serving.types import ModelServiceDefinition


@dataclass
class VFolderInfo:
    """VFolder information for deployment."""

    vfolder_id: UUID
    vfid: str  # Virtual folder ID for storage operations
    host: str  # Storage host
    ownership_type: VFolderOwnershipType


@dataclass
class DeploymentPreparationData:
    """All data needed for deployment preparation."""

    vfolder_info: VFolderInfo
    group_id: Optional[UUID]
    is_endpoint_name_unique: bool


@dataclass
class DeploymentFetchResult:
    """Result of fetching deployment data."""

    model_vfolder_id: UUID
    service_definition: Optional[ModelServiceDefinition]  # Parsed service definition
    group_id: UUID

    # Additional metadata (not exposed as Row objects)
    is_vfolder_valid: bool = True


@dataclass
class ImageResolveResult:
    """Result of resolving image for deployment."""

    image_id: UUID
    canonical: str
    architecture: str
