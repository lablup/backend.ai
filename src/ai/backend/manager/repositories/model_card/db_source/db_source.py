"""Database source for model card repository operations."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.common.types import VFolderID, VFolderUsageMode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.model_card.types import (
    BulkModelCardDeleteFailure,
    BulkModelCardDeleteResultData,
    ModelCardData,
    ResourceRequirementEntry,
    VFolderScanData,
)
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.resource import (
    InvalidProjectTypeForModelCard,
    ModelCardNotFound,
    ProjectNotFound,
)
from ai.backend.manager.errors.storage import VFolderDeletionNotAllowed
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    PresetResourceSlotRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import (
    DEAD_VFOLDER_STATUSES,
    VFolderRow,
    get_sessions_by_mounted_folder,
)
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.updater import (
    Updater,
    execute_updater,
)
from ai.backend.manager.repositories.base.upserter import BulkUpserter, execute_bulk_upserter
from ai.backend.manager.repositories.model_card.types import (
    AvailablePresetsSearchResult,
    ModelCardSearchResult,
    ProjectModelCardSearchScope,
)
from ai.backend.manager.repositories.model_card.updaters import ModelCardUpdaterSpec
from ai.backend.manager.repositories.model_card.upserters import ModelCardScanUpserterSpec
from ai.backend.manager.repositories.vfolder.updaters import VFolderTrashUpdaterSpec
from ai.backend.manager.types import TriState

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelCardDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(self, creator: RBACEntityCreator[ModelCardRow]) -> ModelCardData:
        async with self._db.begin_session() as session:
            result = await execute_rbac_entity_creator(session, creator)
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
            # execute_updater returns the current row even when build_values() is empty
            # (e.g. a child-only update that syncs model_card_resource_requirements), and
            # None only when the row is missing.
            if result is None:
                raise ModelCardNotFound(f"Model card with ID {updater.pk_value} not found.")
            row = result.row

            # Sync the normalized model_card_resource_requirements table when
            # the updater spec requests a change. Plain column UPDATE cannot
            # touch this child table, so we delete-then-insert explicitly.
            if isinstance(updater.spec, ModelCardUpdaterSpec):
                await self._apply_min_resource_change(session, row.id, updater.spec.min_resource)
                if updater.spec.min_resource.is_update() or updater.spec.min_resource.is_nullify():
                    # Re-read so to_data() reflects the new child rows via
                    # the resource_requirement_rows relationship.
                    await session.refresh(row)

            return row.to_data()

    async def _apply_min_resource_change(
        self,
        session: SASession,
        card_id: UUID,
        min_resource: TriState[list[ResourceRequirementEntry]],
    ) -> None:
        """Replace normalized requirement rows for the card when requested.

        NOP  → leave existing rows alone.
        NULLIFY → delete every requirement for the card.
        UPDATE → delete-then-insert with the provided list.
        """
        if min_resource.is_nop():
            return

        await session.execute(
            sa.delete(ModelCardResourceRequirementRow).where(
                ModelCardResourceRequirementRow.model_card_id == card_id
            )
        )

        if min_resource.is_nullify():
            return

        entries = min_resource.value()
        if not entries:
            return

        rows: list[dict[str, object]] = []
        for entry in entries:
            try:
                quantity = Decimal(entry.min_quantity)
            except (InvalidOperation, ValueError):
                log.warning(
                    "model card update: skipping invalid min_quantity {!r} for card {} slot {}",
                    entry.min_quantity,
                    card_id,
                    entry.slot_name,
                )
                continue
            rows.append({
                "model_card_id": card_id,
                "slot_name": entry.slot_name,
                "min_quantity": quantity,
            })
        if rows:
            await session.execute(sa.insert(ModelCardResourceRequirementRow).values(rows))

    async def delete(
        self,
        purger: Purger[ModelCardRow],
        options: DeleteModelCardOptions,
    ) -> UUID:
        async with self._db.begin_session() as session:
            return await self._delete_card_in_session(session, purger, options)

    async def bulk_delete(
        self,
        purgers: list[Purger[ModelCardRow]],
        options: DeleteModelCardOptions,
    ) -> BulkModelCardDeleteResultData:
        """Hard-delete every card behind ``purgers`` with partial-failure semantics.

        Each card runs in its own savepoint so that a single failure (missing
        card, mounted VFolder, ...) does not abort the rest of the batch. The
        outer transaction commits the union of every successful savepoint.
        """
        successes: list[UUID] = []
        failures: list[BulkModelCardDeleteFailure] = []
        if not purgers:
            return BulkModelCardDeleteResultData(successes=successes, failures=failures)
        async with self._db.begin_session() as session:
            for purger in purgers:
                # ModelCardRow uses a UUID primary key; the Purger generic type permits
                # UUID/str/int so narrow it once for the failure record.
                card_id = cast(UUID, purger.pk_value)
                try:
                    async with session.begin_nested():
                        deleted_id = await self._delete_card_in_session(session, purger, options)
                    successes.append(deleted_id)
                except Exception as exc:
                    failures.append(BulkModelCardDeleteFailure(card_id=card_id, message=str(exc)))
        return BulkModelCardDeleteResultData(successes=successes, failures=failures)

    async def _delete_card_in_session(
        self,
        session: SASession,
        purger: Purger[ModelCardRow],
        options: DeleteModelCardOptions,
    ) -> UUID:
        result = await execute_purger(session, purger)
        if result is None:
            raise ModelCardNotFound()
        deleted_row = result.row
        if options.delete_associated_vfolder:
            # The VFolder is going to trash, so any sibling model card pointing
            # at it would be orphaned. Reject up front if the vfolder is still
            # mounted, then hard-delete the siblings and flip the VFolder
            # status atomically — this avoids wasted sibling deletions that
            # would only get rolled back on a mount-check failure.
            vfolder_id = cast(UUID, deleted_row.vfolder)
            await self._reject_if_vfolders_mounted(session, [vfolder_id])
            sibling_result = await session.execute(
                sa.delete(ModelCardRow).where(ModelCardRow.vfolder == vfolder_id)
            )
            sibling_count = cast(CursorResult[Any], sibling_result).rowcount
            if sibling_count:
                # Deleting one card can fan out to N when the vfolder is shared
                # — surface that for ops/debugging since the caller only asked
                # for a single id.
                log.debug(
                    "model card delete: cascaded {} sibling card(s) on vfolder {} "
                    "alongside target {}",
                    sibling_count,
                    vfolder_id,
                    deleted_row.id,
                )
            await execute_updater(
                session, Updater(spec=VFolderTrashUpdaterSpec(), pk_value=vfolder_id)
            )
        return deleted_row.id

    async def _reject_if_vfolders_mounted(
        self,
        session: SASession,
        vfolder_ids: Sequence[UUID],
    ) -> None:
        """Raise :class:`VFolderDeletionNotAllowed` if any VFolder is mounted on a live session.

        Reuses :func:`get_sessions_by_mounted_folder` per-vfolder so the
        rejection message matches :meth:`VFolderRepository.move_vfolders_to_trash`.
        """
        if not vfolder_ids:
            return
        vfolder_rows = (
            (await session.execute(sa.select(VFolderRow).where(VFolderRow.id.in_(vfolder_ids))))
            .scalars()
            .all()
        )
        for vfolder_row in vfolder_rows:
            mount_sessions = await get_sessions_by_mounted_folder(
                session, VFolderID.from_row(vfolder_row)
            )
            if mount_sessions:
                session_ids = [str(session_id) for session_id in mount_sessions]
                raise VFolderDeletionNotAllowed(
                    "Cannot delete the vfolder. "
                    f"The vfolder(id: {vfolder_row.id}) is mounted on sessions(ids: {session_ids})."
                )

    async def search(
        self,
        querier: BatchQuerier,
    ) -> ModelCardSearchResult:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ModelCardRow)
            result = await execute_batch_querier(db_sess, query, querier)
            return ModelCardSearchResult(
                items=[row.ModelCardRow.to_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_in_project(
        self,
        querier: BatchQuerier,
        scope: ProjectModelCardSearchScope,
    ) -> ModelCardSearchResult:
        async with self._db.begin_readonly_session() as db_sess:
            is_member = (await db_sess.execute(scope.membership_check_query)).scalar()
            if not is_member:
                raise GenericForbidden("User is not a member of this project")
            query = sa.select(ModelCardRow)
            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])
            return ModelCardSearchResult(
                items=[row.ModelCardRow.to_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_available_presets(
        self,
        model_card_id: UUID,
        search_input: SearchDeploymentRevisionPresetsInput,
    ) -> AvailablePresetsSearchResult:
        """Find presets whose resource_slots satisfy the model card's min_resource requirements.

        Uses relational division: a preset is "available" iff for every required slot_name
        in model_card_resource_requirements, there exists a matching row in
        preset_resource_slots with quantity >= min_quantity.
        """
        mcr = ModelCardResourceRequirementRow.__table__
        prs = PresetResourceSlotRow.__table__
        drp = DeploymentRevisionPresetRow.__table__

        # Relational division: a preset is "available" iff for every required
        # slot in model_card_resource_requirements there is a matching
        # preset_resource_slot row whose quantity meets the requirement.
        #
        # Both sub-EXISTS clauses must correlate against the OUTER drp/mcr,
        # otherwise SQLAlchemy injects fresh aliases into the inner FROM clause
        # and the predicates degenerate into Cartesian-product matches that
        # accept every preset.
        satisfying_condition = ~sa.exists(
            sa.select(sa.literal(1))
            .select_from(mcr)
            .correlate(drp)
            .where(
                mcr.c.model_card_id == model_card_id,
                ~sa.exists(
                    sa.select(sa.literal(1))
                    .select_from(prs)
                    .correlate(drp, mcr)
                    .where(
                        prs.c.preset_id == drp.c.id,
                        prs.c.slot_name == mcr.c.slot_name,
                        prs.c.quantity >= mcr.c.min_quantity,
                    )
                ),
            )
        )

        async with self._db.begin_readonly_session() as db_sess:
            count_stmt = sa.select(sa.func.count()).select_from(drp).where(satisfying_condition)
            total_count = (await db_sess.execute(count_stmt)).scalar() or 0

            query = sa.select(DeploymentRevisionPresetRow).where(satisfying_condition)

            offset = search_input.offset or 0
            limit = search_input.limit or 20
            query = query.offset(offset).limit(limit + 1)

            result = await db_sess.execute(query)
            rows = list(result.scalars().all())

            has_next_page = len(rows) > limit
            if has_next_page:
                rows = rows[:limit]

            return AvailablePresetsSearchResult(
                items=[row.to_data() for row in rows],
                total_count=total_count,
                has_next_page=has_next_page,
                has_previous_page=offset > 0,
            )

    async def get_scan_target_vfolders(self, project_id: UUID) -> list[VFolderScanData]:
        async with self._db.begin_readonly_session() as session:
            project_stmt = sa.select(GroupRow.type).where(GroupRow.id == project_id)
            project_type = (await session.execute(project_stmt)).scalar_one_or_none()
            if project_type is None:
                raise ProjectNotFound(str(project_id))
            if project_type != ProjectType.MODEL_STORE:
                raise InvalidProjectTypeForModelCard(
                    extra_msg=f"Project {project_id} is type '{project_type}', expected 'model-store'"
                )
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

            # Resolve all upserted card ids by name so we can sync RBAC bindings
            # and the normalized resource requirement child rows below.
            all_card_rows = (
                await session.execute(
                    sa.select(ModelCardRow.id, ModelCardRow.name).where(
                        sa.and_(
                            ModelCardRow.name.in_({s.name for s in specs}),
                            ModelCardRow.project == specs[0].project_id,
                            ModelCardRow.domain == specs[0].domain,
                        )
                    )
                )
            ).all()
            name_to_card_id: dict[str, UUID] = {row.name: row.id for row in all_card_rows}

            # Bind all upserted model cards to their project scope in RBAC
            # ON CONFLICT DO NOTHING ensures idempotency for existing bindings
            new_names = {s.name for s in specs} - existing_names
            if new_names:
                new_card_rows = [row for row in all_card_rows if row.name in new_names]
                if new_card_rows:
                    assoc_values = [
                        {
                            "scope_type": RBACElementType.PROJECT.to_scope_type(),
                            "scope_id": str(specs[0].project_id),
                            "entity_type": RBACElementType.MODEL_CARD.to_entity_type(),
                            "entity_id": str(row.id),
                            "relation_type": RelationType.AUTO,
                        }
                        for row in new_card_rows
                    ]
                    await session.execute(
                        pg_insert(AssociationScopesEntitiesRow)
                        .values(assoc_values)
                        .on_conflict_do_nothing()
                    )

            # Sync the normalized model_card_resource_requirements child rows.
            # The bulk upserter only writes the model_cards table itself; without
            # this step search_available_presets sees an empty requirements table
            # and degrades into a vacuous-truth filter that returns every preset.
            # Use delete-then-insert per card so re-scan stays idempotent (same
            # input → same row count, no duplication).
            await self._sync_model_card_resource_requirements(session, specs, name_to_card_id)

            return created, updated

    async def _sync_model_card_resource_requirements(
        self,
        session: SASession,
        specs: Sequence[ModelCardScanUpserterSpec],
        name_to_card_id: dict[str, UUID],
    ) -> None:
        """Replace child rows for every (model_card, slot) requirement.

        Idempotent: re-running with the same specs leaves the row count
        unchanged. Decimal-coerced values are stored in the Numeric column.
        """
        target_card_ids = [
            name_to_card_id[spec.name] for spec in specs if spec.name in name_to_card_id
        ]
        if not target_card_ids:
            return

        # Drop the old set of requirements for the cards we are about to write.
        await session.execute(
            sa.delete(ModelCardResourceRequirementRow).where(
                ModelCardResourceRequirementRow.model_card_id.in_(target_card_ids)
            )
        )

        new_rows: list[dict[str, object]] = []
        for spec in specs:
            card_id = name_to_card_id.get(spec.name)
            if card_id is None:
                continue
            for entry in spec.min_resource:
                try:
                    quantity = Decimal(entry.min_quantity)
                except (InvalidOperation, ValueError):
                    log.warning(
                        "model card scan: skipping invalid min_quantity {!r} for card {} slot {}",
                        entry.min_quantity,
                        card_id,
                        entry.slot_name,
                    )
                    continue
                new_rows.append({
                    "model_card_id": card_id,
                    "slot_name": entry.slot_name,
                    "min_quantity": quantity,
                })

        if new_rows:
            await session.execute(sa.insert(ModelCardResourceRequirementRow).values(new_rows))
