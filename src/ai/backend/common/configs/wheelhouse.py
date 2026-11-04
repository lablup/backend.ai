from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import BackendAIConfigMeta, ConfigExample

__all__ = ("WheelhouseConfig",)


class WheelhouseConfig(BaseConfigSchema):
    """Configuration for loading plugin wheels from a directory when a server starts."""

    allow: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Whether to load the plugin wheels in the path when the server starts. "
                "A config file found through the current directory cannot turn this on: "
                "name it with the -f option or BACKEND_CONFIG_FILE."
            ),
            added_version="26.10.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    path: Annotated[
        Path,
        Field(default=Path("/opt/backend.ai/wheelhouse")),
        BackendAIConfigMeta(
            description=(
                "Absolute path of the directory holding the plugin wheels. "
                "A relative path is rejected so that the current directory cannot choose it."
            ),
            added_version="26.10.0",
            example=ConfigExample(
                local="/opt/backend.ai/wheelhouse", prod="/opt/backend.ai/wheelhouse"
            ),
        ),
    ]

    @field_validator("path")
    @classmethod
    def _reject_relative_path(cls, path: Path) -> Path:
        if not path.is_absolute():
            raise ValueError("wheelhouse.path must be an absolute path")
        return path
