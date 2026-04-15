"""Admin repository for deployment maintenance operations."""

from __future__ import annotations

import logging
from typing import Any, cast

from ruamel.yaml import YAML

from ai.backend.common.config import ModelDefinition
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    RevisionModelDefinitionUpdate,
    RevisionSyncResult,
)
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.repositories.deployment.storage_source import DeploymentStorageSource

from .db_source import DeploymentDBSource

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeploymentAdminRepository:
    """Repository for admin-only deployment maintenance operations."""

    _db_source: DeploymentDBSource
    _storage_source: DeploymentStorageSource

    def __init__(
        self,
        db_source: DeploymentDBSource,
        storage_source: DeploymentStorageSource,
    ) -> None:
        self._db_source = db_source
        self._storage_source = storage_source

    async def sync_model_definitions(self) -> list[RevisionSyncResult]:
        """Sync model_definition from vfolder storage for all revisions with a model vfolder.

        Compares the stored model_definition with the current vfolder file content
        and updates the DB when they differ (including NULL -> populated).

        Returns:
            List of per-revision sync results
        """
        yaml = YAML()
        results: list[RevisionSyncResult] = []

        rows = await self._db_source.get_revisions_with_vfolder_info()

        batch_updates: list[RevisionModelDefinitionUpdate] = []

        for row in rows:
            vfolder_location = VFolderLocation(
                id=row.vfolder_id,
                quota_scope_id=row.vfolder_quota_scope_id,
                host=row.vfolder_host,
                ownership_type=row.vfolder_ownership_type,
                usage_mode=row.vfolder_usage_mode,
            )
            candidates = (
                [row.model_definition_path]
                if row.model_definition_path
                else ["model-definition.yaml", "model-definition.yml"]
            )
            try:
                raw_bytes = await self._storage_source.fetch_definition_file(
                    vfolder_location, candidates
                )
                raw_dict: dict[str, Any] = cast(dict[str, Any], yaml.load(raw_bytes))
                model_def = ModelDefinition.model_validate(raw_dict)
            except Exception as e:
                log.warning(
                    "Failed to fetch model definition for revision {} (vfolder {})",
                    row.revision_id,
                    row.vfolder_id,
                    exc_info=True,
                )
                results.append(
                    RevisionSyncResult(
                        revision_id=row.revision_id, success=False, failure_reason=str(e)
                    )
                )
                continue

            stored = (
                ModelDefinition.model_validate(row.model_definition)
                if row.model_definition is not None
                else None
            )
            if stored == model_def:
                continue

            batch_updates.append(
                RevisionModelDefinitionUpdate(
                    revision_id=row.revision_id, model_definition=model_def
                )
            )

        if batch_updates:
            await self._db_source.batch_update_model_definitions(batch_updates)
            for update in batch_updates:
                results.append(RevisionSyncResult(revision_id=update.revision_id, success=True))

        return results
