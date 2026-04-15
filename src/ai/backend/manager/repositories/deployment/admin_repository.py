"""Admin repository for deployment maintenance operations."""

from __future__ import annotations

import logging
import uuid
from typing import Any, cast

from ruamel.yaml import YAML

from ai.backend.common.config import ModelDefinition
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.repositories.deployment.storage_source import DeploymentStorageSource
from ai.backend.manager.services.deployment.actions.sync_model_definitions import (
    RevisionSyncStatus,
)

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

    async def sync_model_definitions(self) -> list[RevisionSyncStatus]:
        """Sync model_definition from vfolder storage for all revisions with a model vfolder.

        Compares the stored model_definition with the current vfolder file content
        and updates the DB when they differ (including NULL -> populated).

        Returns:
            List of per-revision sync statuses
        """
        yaml = YAML()
        results: list[RevisionSyncStatus] = []

        rows = await self._db_source.get_revisions_with_vfolder_info()

        pending_updates: list[tuple[uuid.UUID, dict[str, Any]]] = []

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
                    RevisionSyncStatus(revision_id=row.revision_id, success=False, reason=str(e))
                )
                continue

            model_def_dict = model_def.model_dump(exclude_none=True, by_alias=True)
            if row.model_definition == model_def_dict:
                continue

            pending_updates.append((row.revision_id, model_def_dict))

        if pending_updates:
            await self._db_source.batch_update_model_definitions(pending_updates)
            for revision_id, _ in pending_updates:
                results.append(RevisionSyncStatus(revision_id=revision_id, success=True))

        return results
