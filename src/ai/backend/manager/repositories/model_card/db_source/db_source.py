"""Database source for model card repository operations."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.types import VFolderUsageMode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.model_card.types import ModelCardData, VFolderScanData
from ai.backend.manager.errors.resource import ModelCardNotFound, ProjectNotFound
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import DEAD_VFOLDER_STATUSES, VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.base.upserter import BulkUpserter, execute_bulk_upserter
from ai.backend.manager.repositories.model_card.upserters import ModelCardScanUpserterSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelCardDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(self, creator: Creator[ModelCardRow]) -> ModelCardData:
        async with self._db.begin_session() as session:
            result = await execute_creator(session, creator)
            return result.row.to_data()

    async def get_by_id(self, card_id: UUID) -> ModelCardData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ModelCardRow).where(ModelCardRow.id == card_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise ModelCardNotFound()
            return row.to_data()

    async def update(self, updater: Updater[ModelCardRow]) -> ModelCardData:
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise ModelCardNotFound(f"Model card with ID {updater.pk_value} not found.")
            return result.row.to_data()

    async def delete(self, card_id: UUID) -> ModelCardData:
        async with self._db.begin_session() as session:
            stmt = sa.select(ModelCardRow).where(ModelCardRow.id == card_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise ModelCardNotFound()
            data = row.to_data()
            await session.delete(row)
        return data

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[ModelCardData], int, bool, bool]:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ModelCardRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.ModelCardRow.to_data() for row in result.rows]
            return items, result.total_count, result.has_next_page, result.has_previous_page

    async def get_scan_target_vfolders(self, project_id: UUID) -> list[VFolderScanData]:
        async with self._db.begin_readonly_session() as session:
            project_stmt = sa.select(GroupRow.type).where(GroupRow.id == project_id)
            project_type = (await session.execute(project_stmt)).scalar_one_or_none()
            if project_type is None:
                raise ProjectNotFound(str(project_id))
            if project_type != ProjectType.MODEL_STORE:
                raise ProjectNotFound(f"Project {project_id} is not a MODEL_STORE type project")
            stmt = sa.select(VFolderRow).where(
                sa.and_(
                    VFolderRow.group == project_id,
                    VFolderRow.usage_mode == VFolderUsageMode.MODEL,
                    VFolderRow.status.not_in(DEAD_VFOLDER_STATUSES),
                )
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [
                VFolderScanData(
                    id=row.id,
                    name=row.name,
                    host=row.host,
                    quota_scope_id=row.quota_scope_id,
                    unmanaged_path=row.unmanaged_path,
                    domain_name=row.domain_name,
                    project_id=row.group,
                )
                for row in rows
                if row.group is not None
            ]

    async def get_existing_card_names(self, project_id: UUID, domain: str) -> set[str]:
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ModelCardRow.name).where(
                sa.and_(
                    ModelCardRow.project == project_id,
                    ModelCardRow.domain == domain,
                )
            )
            rows = (await session.scalars(stmt)).all()
            return set(rows)

    async def bulk_upsert_scan(
        self,
        specs: Sequence[ModelCardScanUpserterSpec],
        existing_names: set[str],
    ) -> tuple[int, int]:
        if not specs:
            return 0, 0
        async with self._db.begin_session() as session:
            bulk_upserter: BulkUpserter[ModelCardRow] = BulkUpserter(specs=specs)
            result = await execute_bulk_upserter(
                session, bulk_upserter, index_elements=["name", "domain", "project"]
            )
            total = result.upserted_count
            updated = sum(1 for s in specs if s.name in existing_names)
            created = total - updated
            return created, updated
