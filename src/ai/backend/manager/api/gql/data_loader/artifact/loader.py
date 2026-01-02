from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.repositories.artifact.options import ArtifactConditions
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.artifact.actions.search import SearchArtifactsAction
from ai.backend.manager.services.artifact.processors import ArtifactProcessors


async def load_artifacts_by_ids(
    processor: ArtifactProcessors,
    artifact_ids: Sequence[uuid.UUID],
) -> list[Optional[ArtifactData]]:
    """Batch load artifacts by their IDs.

    Args:
        processor: The artifact processor.
        artifact_ids: Sequence of artifact UUIDs to load.

    Returns:
        List of ArtifactData (or None if not found) in the same order as artifact_ids.
    """
    if not artifact_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(artifact_ids)),
        conditions=[ArtifactConditions.by_ids(artifact_ids)],
    )

    action_result = await processor.search_artifacts.wait_for_complete(
        SearchArtifactsAction(querier=querier)
    )

    artifact_map = {artifact.id: artifact for artifact in action_result.data}
    return [artifact_map.get(artifact_id) for artifact_id in artifact_ids]
