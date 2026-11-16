from __future__ import annotations

from typing import Annotated

from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import (
    NEXT_RELEASE_VERSION,
    BackendAIConfigMeta,
    CompositeType,
    ConfigExample,
)


class VolumeDeclarationConfig(BaseConfigSchema):
    interval: Annotated[
        float,
        Field(default=30.0, gt=0),
        BackendAIConfigMeta(
            description="Seconds between two reads of the agent's volume declarations from Valkey.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="30", prod="30"),
        ),
    ]
    initial_delay: Annotated[
        float,
        Field(
            default=0.0,
            ge=0,
            validation_alias=AliasChoices("initial-delay", "initial_delay"),
            serialization_alias="initial-delay",
        ),
        BackendAIConfigMeta(
            description="Seconds to wait before the first read of the agent's volume declarations.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="0", prod="0"),
        ),
    ]


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
    read_declaration: Annotated[
        VolumeDeclarationConfig,
        Field(
            default_factory=VolumeDeclarationConfig,
            validation_alias=AliasChoices("read-declaration", "read_declaration"),
            serialization_alias="read-declaration",
        ),
        BackendAIConfigMeta(
            description=(
                "Configuration for the periodic read of the agent's volume declarations, "
                "which decides the volumes the agent checks."
            ),
            added_version=NEXT_RELEASE_VERSION,
            composite=CompositeType.FIELD,
        ),
    ]
