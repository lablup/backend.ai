from __future__ import annotations

from typing import Annotated

from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample


class StorageStatusReportConfig(BaseConfigSchema):
    interval: Annotated[
        float,
        Field(default=30.0, gt=0),
        BackendAIConfigMeta(
            description="Seconds between two storage status reports to the manager.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="30", prod="30"),
        ),
    ]
    initial_delay: Annotated[
        float,
        Field(
            default=10.0,
            ge=0,
            validation_alias=AliasChoices("initial-delay", "initial_delay"),
            serialization_alias="initial-delay",
        ),
        BackendAIConfigMeta(
            description="Seconds to wait before the first storage status report.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="10", prod="10"),
        ),
    ]
