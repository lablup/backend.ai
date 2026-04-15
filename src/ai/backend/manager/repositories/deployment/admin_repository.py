"""Admin repository for deployment maintenance operations."""

from __future__ import annotations

import logging
import uuid
from typing import Any, cast

import sqlalchemy as sa
from ruamel.yaml import YAML

from ai.backend.common.config import ModelDefinition
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.deployment.storage_source import DeploymentStorageSource

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeploymentAdminRepository:
    """Repository for admin-only deployment maintenance operations."""

    _db: ExtendedAsyncSAEngine
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._db = db
        self._storage_manager = storage_manager

    async def sync_model_definitions(self) -> tuple[int, int]:
        """Sync model_definition from vfolder storage for all revisions with a model vfolder.

        Compares the stored model_definition with the current vfolder file content
        and updates the DB when they differ (including NULL -> populated).

        Returns:
            Tuple of (updated_count, failed_count)
        """
        storage_source = DeploymentStorageSource(self._storage_manager)
        yaml = YAML()
        updated = 0
        failed = 0

        async with self._db.begin_readonly_session() as session:
            rows = (
                await session.execute(
                    sa.select(
                        DeploymentRevisionRow.id,
                        DeploymentRevisionRow.model,
                        DeploymentRevisionRow.model_definition,
                        DeploymentRevisionRow.model_definition_path,
                        VFolderRow.id.label("vf_id"),
                        VFolderRow.quota_scope_id.label("vf_quota_scope_id"),
                        VFolderRow.host.label("vf_host"),
                        VFolderRow.ownership_type.label("vf_ownership_type"),
                        VFolderRow.usage_mode.label("vf_usage_mode"),
                    )
                    .select_from(
                        sa.join(
                            DeploymentRevisionRow.__table__,
                            VFolderRow.__table__,
                            DeploymentRevisionRow.model == VFolderRow.id,
                        )
                    )
                    .where(
                        DeploymentRevisionRow.model.is_not(None),
                    )
                )
            ).all()

        for row in rows:
            revision_id: uuid.UUID = row.id
            vfolder_location = VFolderLocation(
                id=row.vf_id,
                quota_scope_id=row.vf_quota_scope_id,
                host=row.vf_host,
                ownership_type=row.vf_ownership_type,
                usage_mode=row.vf_usage_mode,
            )
            candidates = (
                [row.model_definition_path]
                if row.model_definition_path
                else ["model-definition.yaml", "model-definition.yml"]
            )
            try:
                raw_bytes = await storage_source.fetch_definition_file(vfolder_location, candidates)
                raw_dict: dict[str, Any] = cast(dict[str, Any], yaml.load(raw_bytes))
                model_def = ModelDefinition.model_validate(raw_dict)
            except Exception:
                log.warning(
                    "Failed to fetch model definition for revision {} (vfolder {})",
                    revision_id,
                    row.vf_id,
                )
                failed += 1
                continue

            model_def_dict = model_def.model_dump(exclude_none=True, by_alias=True)
            if row.model_definition == model_def_dict:
                continue

            async with self._db.begin_session() as session:
                await session.execute(
                    sa.update(DeploymentRevisionRow.__table__)
                    .where(DeploymentRevisionRow.id == revision_id)
                    .values(model_definition=model_def_dict)
                )
            updated += 1

        return updated, failed
