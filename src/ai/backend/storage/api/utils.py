from __future__ import annotations

from typing import Optional

from ai.backend.common.data.storage.types import ArtifactStorageImportStep


def get_storage_step_mappings(
    storage_per_steps: Optional[dict[ArtifactStorageImportStep, str]],
    fallback_storage: str,
) -> dict[ArtifactStorageImportStep, str]:
    if storage_per_steps is not None:
        return storage_per_steps
    else:
        # Use storage_name as fallback for all steps
        return {
            ArtifactStorageImportStep.DOWNLOAD: fallback_storage,
            ArtifactStorageImportStep.ARCHIVE: fallback_storage,
        }
