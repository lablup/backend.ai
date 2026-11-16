from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample

__all__ = ("WheelhouseConfig",)


class WheelhouseConfig(BaseConfigSchema):
    """Configuration for loading plugin wheels from a directory when a server starts."""

    allow: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=("Whether to load the plugin wheels in the path when the server starts."),
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    path: Annotated[
        Path,
        Field(default=Path("wheelhouse")),
        BackendAIConfigMeta(
            description=(
                "Directory holding the plugin wheels. A relative path starts from the current "
                "directory of the server. The storage-proxy runs from the directory of its "
                "config file."
            ),
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="wheelhouse", prod="wheelhouse"),
        ),
    ]
