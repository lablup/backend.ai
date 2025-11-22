from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from ai.backend.common.data.model_card import ModelDefinition
from ai.backend.common.types import VFolderOperationStatus


@dataclass(frozen=True)
class ModelCardData:
    """
    Complete model card data including VFolder information and parsed metadata.
    """

    # VFolder base information
    id: UUID
    host: Optional[str] = None
    name: Optional[str] = None
    creator: Optional[str] = None
    created_at: Optional[datetime] = None
    status: Optional[VFolderOperationStatus] = None

    # Model definition
    model_definition: Optional[ModelDefinition] = None

    # Metadata (flattened for convenience)
    author: Optional[str] = None
    title: Optional[str] = None
    version: Optional[str] = None
    modified_at: Optional[datetime] = None
    description: Optional[str] = None
    task: Optional[str] = None
    category: Optional[str] = None
    architecture: Optional[str] = None
    framework: Optional[list[str]] = None
    label: Optional[list[str]] = None
    license: Optional[str] = None
    min_resource: Optional[Mapping[str, Any]] = None

    # README information
    readme: Optional[str] = None
    readme_filetype: Optional[str] = None

    # Error information
    error_msg: Optional[str] = None
