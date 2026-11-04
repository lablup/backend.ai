from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample

__all__ = ("WheelhouseConfig",)


class WheelhouseConfig(BaseConfigSchema):
    """Configuration for loading plugin wheels from a directory when a server starts."""

    allow: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Whether to load the plugin wheels in the path when the server starts. "
                "Only a config file named with the -f option, or found in "
                "~/.config/backend.ai or /etc/backend.ai, can turn this on."
            ),
            added_version=NEXT_RELEASE_VERSION,
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
            added_version=NEXT_RELEASE_VERSION,
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
