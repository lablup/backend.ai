from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.repositories.artifact.options import ArtifactRevisionConditions
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.artifact_revision.actions.search import (
    SearchArtifactRevisionsAction,
)
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors


async def load_artifact_revisions_by_ids(
    processor: ArtifactRevisionProcessors,
    revision_ids: Sequence[uuid.UUID],
) -> list[Optional[ArtifactRevisionData]]:
    """Batch load artifact revisions by their IDs.

    Args:
        processor: The artifact revision processor.
        revision_ids: Sequence of revision UUIDs to load.

    Returns:
        List of ArtifactRevisionData (or None if not found) in the same order as revision_ids.
    """
    if not revision_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(revision_ids)),
        conditions=[ArtifactRevisionConditions.by_ids(revision_ids)],
    )

    action_result = await processor.search_revision.wait_for_complete(
        SearchArtifactRevisionsAction(querier=querier)
    )

    revision_map = {revision.id: revision for revision in action_result.data}
    return [revision_map.get(revision_id) for revision_id in revision_ids]
