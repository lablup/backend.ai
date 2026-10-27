from __future__ import annotations

from typing import Annotated

from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample


class VolumeStatusCheckConfig(BaseConfigSchema):
    check_interval: Annotated[
        float,
        Field(
            default=30.0,
            gt=0,
            validation_alias=AliasChoices("check-interval", "check_interval"),
            serialization_alias="check-interval",
        ),
        BackendAIConfigMeta(
            description="Seconds between two status checks of a volume.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="60", prod="60"),
        ),
    ]
    initial_delay: Annotated[
        float,
        Field(
            default=5.0,
            ge=0,
            validation_alias=AliasChoices("initial-delay", "initial_delay"),
            serialization_alias="initial-delay",
        ),
        BackendAIConfigMeta(
            description="Seconds to wait before the first status check of a volume.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="5", prod="5"),
        ),
    ]
