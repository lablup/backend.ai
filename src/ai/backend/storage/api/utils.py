from __future__ import annotations

from typing import Optional

from ai.backend.common.data.storage.types import ArtifactStorageImportStep


def create_storage_step_mappings(
    storage_step_mappings: Optional[dict[ArtifactStorageImportStep, str]],
    fallback_storage_name: str,
) -> dict[ArtifactStorageImportStep, str]:
    """Create storage step mappings, using fallback storage if not provided."""
    if storage_step_mappings is not None:
        return storage_step_mappings
    else:
        # Use storage_name as fallback for all steps
        return {
            ArtifactStorageImportStep.DOWNLOAD: fallback_storage_name,
            ArtifactStorageImportStep.ARCHIVE: fallback_storage_name,
        }
