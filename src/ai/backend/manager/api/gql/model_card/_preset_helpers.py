"""Internal helpers shared between the model_card root resolver and the
ModelCardGQL field resolver for available presets."""

from __future__ import annotations

from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.manager.api.gql.deployment.types.revision_preset import (
    DeploymentRevisionPresetConnection,
    DeploymentRevisionPresetEdge,
    DeploymentRevisionPresetGQL,
)


def build_preset_connection(
    result: SearchDeploymentRevisionPresetsPayload,
) -> DeploymentRevisionPresetConnection:
    """Convert an adapter payload into a Relay connection of preset nodes.

    Used by both ``model_card_available_presets`` (root query) and
    ``ModelCardGQL.available_presets`` (field resolver) to keep their output
    shape identical.
    """
    edges = [
        DeploymentRevisionPresetEdge(
            node=DeploymentRevisionPresetGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return DeploymentRevisionPresetConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
