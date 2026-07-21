from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample

__all__ = ("MemrayConfig",)


class MemrayConfig(BaseConfigSchema):
    """Configuration for memray memory-allocation tracking.

    Memray captures every allocation made by the process, which is useful for
    diagnosing memory growth but adds significant runtime and disk overhead.
    Enable it only while investigating a memory issue.
    """

    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Whether to track memory allocations with memray. "
                "The capture file grows continuously while the process runs, so keep this "
                "disabled unless you are actively debugging memory usage."
            ),
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    output_destination: Annotated[
        Path,
        Field(
            default=Path("./memray-output.bin"),
            validation_alias=AliasChoices("output-destination", "output_destination"),
            serialization_alias="output-destination",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to store the memray allocation capture. "
                "Memray refuses to start when the file already exists, so the process appends "
                "its PID to the path. Ensure the parent directory exists and has enough space."
            ),
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(
                local="./memray-output.bin",
                prod="/var/log/backend.ai/memray/output.bin",
            ),
        ),
    ]
    native_traces: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("native-traces", "native_traces"),
            serialization_alias="native-traces",
        ),
        BackendAIConfigMeta(
            description=(
                "Whether to also capture native (C/C++) call stacks, so that allocations made "
                "inside extension modules are attributed to their native frames instead of the "
                "calling Python frame. This adds runtime overhead and enlarges the capture, and "
                "the native frames only resolve when debug symbols are available."
            ),
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
