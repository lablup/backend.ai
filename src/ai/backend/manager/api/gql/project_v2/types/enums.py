"""ProjectV2 GraphQL enum types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_enum


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Project type determining its purpose and behavior. "
            "GENERAL: Standard project for general computation. "
            "MODEL_STORE: Project for model storage and management."
        ),
    ),
    name="ProjectTypeV2",
)
class ProjectTypeEnum(StrEnum):
    """Project type enum."""

    GENERAL = "general"
    MODEL_STORE = "model-store"
