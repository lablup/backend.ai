from __future__ import annotations

from pathlib import Path
from typing import Annotated, Final

from pydantic import Field

from ai.backend.common.configs.volume.base import VolumeConfig
from ai.backend.common.meta import BackendAIConfigMeta, ConfigExample
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

DEFAULT_VOLUME_MARKER_FILENAME: Final = ".backend.ai-volume-id"


class VfsVolumeConfig(VolumeConfig):
    path: Annotated[
        Path,
        Field(),
        BackendAIConfigMeta(
            description="The mount path the volume is served from.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="vfolder/local/volume1", prod="/mnt/volume1"),
        ),
    ]
    marker_filename: Annotated[
        str,
        Field(default=DEFAULT_VOLUME_MARKER_FILENAME),
        BackendAIConfigMeta(
            description="The file at the mount root an operator writes the volume id into.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(
                local=DEFAULT_VOLUME_MARKER_FILENAME, prod=DEFAULT_VOLUME_MARKER_FILENAME
            ),
        ),
    ]
