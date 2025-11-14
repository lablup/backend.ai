from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelCardMetadata(BaseModel):
    """
    Model card metadata parsed from model-definition.yml/yaml file.
    """

    model_config = ConfigDict(frozen=True)

    author: Optional[str] = None
    title: Optional[str] = None
    version: Optional[str] = None
    created: Optional[datetime] = Field(default=None, description="Model creation timestamp")
    modified: Optional[datetime] = Field(
        default=None, description="Model last modification timestamp"
    )
    description: Optional[str] = None
    task: Optional[str] = Field(
        default=None, description="Task type (e.g., 'classification', 'detection')"
    )
    category: Optional[str] = Field(default=None, description="Model category")
    architecture: Optional[str] = Field(default=None, description="Model architecture name")
    framework: Optional[list[str]] = Field(
        default=None, description="List of frameworks (e.g., ['pytorch', 'tensorflow'])"
    )
    label: Optional[list[str]] = Field(default=None, description="Model labels/tags")
    license: Optional[str] = Field(default=None, description="Model license")
    min_resource: Optional[Mapping[str, Any]] = Field(
        default=None, description="Minimum resource requirements"
    )


class ModelServiceConfig(BaseModel):
    """
    Model service configuration from model-definition file.
    """

    model_config = ConfigDict(frozen=True)

    start_command: str | list[str]
    port: int
    pre_start_actions: Optional[list[dict[str, Any]]] = None
    shell: str = "/bin/bash"
    health_check: Optional[dict[str, Any]] = None


class ModelDefinition(BaseModel):
    """
    Model definition parsed from model-definition.yml/yaml file.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    model_path: str
    service: Optional[ModelServiceConfig] = None
    metadata: Optional[ModelCardMetadata] = None
