from __future__ import annotations

import logging
from typing import Optional

from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def get_storage_step_mappings(
    storage_per_steps: Optional[dict[str, str]],
    fallback_storage: str,
) -> dict[ArtifactStorageImportStep, str]:
    if storage_per_steps is not None:
        # Convert string keys to enum keys
        converted_mappings = {}
        for step_str, storage_name in storage_per_steps.items():
            try:
                step_enum = ArtifactStorageImportStep(step_str)
                converted_mappings[step_enum] = storage_name
            except ValueError:
                # Skip invalid step names
                log.warning(
                    "Ignoring invalid import step name in storage_step_mappings: %s", step_str
                )
                continue
        return converted_mappings
    else:
        # Use storage_name as fallback for all steps
        return {
            ArtifactStorageImportStep.DOWNLOAD: fallback_storage,
            ArtifactStorageImportStep.ARCHIVE: fallback_storage,
        }
