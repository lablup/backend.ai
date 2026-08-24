"""Database source for model card repository operations."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.common.types import VFolderID, VFolderUsageMode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.model_card.types import (
    BulkModelCardDeleteFailure,
    BulkModelCardDeleteResultData,
    ModelCardData,
    ModelCardResourceRequirementData,
    ResourceRequirementEntry,
    VFolderScanData,
)
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.resource import (
    InvalidProjectTypeForModelCard,
    ModelCardNotFound,
    ProjectNotFound,
)
from ai.backend.manager.errors.storage import VFolderDeletionNotAllowed
from ai.backend.manager.models.deployment_revision_preset.conditions import (
    DeploymentRevisionPresetConditions,
)
from ai.backend.manager.models.deployment_revision_preset.searchers import (
    DeploymentPresetSearcher,
)
from ai.backend.manager.models.model_card.creators import ModelCardResourceRequirementCreator
from ai.backend.manager.models.model_card.purgers import (
    ModelCardPurger,
    ModelCardResourceRequirementBatchPurger,
    ModelCardVFolderBatchPurger,
)
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.searchers import ModelCardSearcher
from ai.backend.manager.models.model_card.updaters import ModelCardUpdater
from ai.backend.manager.models.model_card.upserters import ModelCardScanUpserter
from ai.backend.manager.models.project.queriers import ProjectQuerier
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow
from ai.backend.manager.models.session.searchers import LiveSessionsMountingVFolderSearcher
from ai.backend.manager.models.specs.creator import FieldToCreate
from ai.backend.manager.models.specs.pagination import NoPagination, OffsetPagination
from ai.backend.manager.models.vfolder.queriers import VFolderQuerier
from ai.backend.manager.models.vfolder.row import DEAD_VFOLDER_STATUSES, VFolderRow
from ai.backend.manager.models.vfolder.searchers import VFolderScanTargetSearcher
from ai.backend.manager.models.vfolder.updaters import VFolderSoftDeleteUpdater
from ai.backend.manager.repositories.model_card.types import (
    AvailablePresetsSearchResult,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps
from ai.backend.manager.types import TriState

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelCardDBSource:
    _v2_ops: V2DBOpsProvider

    def __init__(self, v2_ops_provider: V2DBOpsProvider) -> None:
        self._v2_ops = v2_ops_provider

    async def update(self, updater: ModelCardUpdater) -> ModelCardData:
        async with self._v2_ops.write_ops() as w:
            # The card comes back even when build_values() is empty (a child-only update
            # that syncs model_card_resource_requirements); None means it is missing.
            data = await w.update_data(updater)
            if data is None:
                raise ModelCardNotFound(f"Model card with ID {updater.card_id} not found.")

            # Plain column UPDATE cannot touch the child table, so replace it explicitly.
            await self._apply_min_resource_change(w, ModelCardID(data.id), updater.min_resource)

            return data

    async def _apply_min_resource_change(
        self,
        w: V2WriteOps,
        card_id: ModelCardID,
        min_resource: TriState[list[ResourceRequirementEntry]],
    ) -> None:
        """Replace normalized requirement rows for the card when requested.

        NOP  -> leave existing rows alone.
        NULLIFY -> delete every requirement for the card.
        UPDATE -> delete-then-insert with the provided list.
        """
        if min_resource.is_nop():
            return
        if min_resource.is_nullify():
            await self._replace_min_resource(w, card_id, [])
            return
        await self._replace_min_resource(w, card_id, min_resource.value())

    async def _replace_min_resource(
        self,
        w: V2WriteOps,
        card_id: ModelCardID,
        entries: Sequence[ResourceRequirementEntry],
    ) -> None:
        """Delete-then-insert the card's requirement rows, so a re-run is idempotent.

        Entries whose ``min_quantity`` is not a decimal are skipped with a warning
        rather than failing the whole write.
        """
        await w.batch_purge_field_entities(card_id, ModelCardResourceRequirementBatchPurger())
        if not entries:
            return

        creations: list[
            FieldToCreate[
                ModelCardID, ModelCardResourceRequirementRow, ModelCardResourceRequirementData
            ]
        ] = []
        for entry in entries:
            try:
                Decimal(entry.min_quantity)
            except (InvalidOperation, ValueError):
                log.warning(
                    "model card update: skipping invalid min_quantity {!r} for card {} slot {}",
                    entry.min_quantity,
                    card_id,
                    entry.slot_name,
                )
                continue
            creations.append(
                FieldToCreate(
                    owner_id=card_id,
                    creator=ModelCardResourceRequirementCreator(entry=entry),
                )
            )
        if creations:
            await w.atomic_create_fields(creations)

    async def delete(
        self,
        purger: ModelCardPurger,
        options: DeleteModelCardOptions,
    ) -> UUID:
        async with self._v2_ops.write_ops() as w:
            return await self._delete_card(w, purger, options)

    async def bulk_delete(
        self,
        purgers: list[ModelCardPurger],
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
        async with self._v2_ops.write_ops() as w:
            for purger in purgers:
                try:
                    async with w.savepoint() as sp:
                        deleted_id = await self._delete_card(sp, purger, options)
                    successes.append(deleted_id)
                except Exception as exc:
                    failures.append(
                        BulkModelCardDeleteFailure(card_id=purger.card_id, message=str(exc))
                    )
        return BulkModelCardDeleteResultData(successes=successes, failures=failures)

    async def _delete_card(
        self,
        w: V2WriteOps,
        purger: ModelCardPurger,
        options: DeleteModelCardOptions,
    ) -> UUID:
        deleted = await w.purge_entity(purger)
        if deleted is None:
            raise ModelCardNotFound()
        if options.delete_associated_vfolder:
            # The VFolder is going to trash, so any sibling model card pointing
            # at it would be orphaned. Reject up front if the vfolder is still
            # mounted, then hard-delete the siblings and flip the VFolder
            # status atomically -- this avoids wasted sibling deletions that
            # would only get rolled back on a mount-check failure.
            vfolder_id = VFolderUUID(deleted.vfolder_id)
            await self._reject_if_vfolder_mounted(w, vfolder_id)
            siblings = await w.batch_purge_entities_in_global(
                ModelCardVFolderBatchPurger(vfolder_id=vfolder_id)
            )
            if siblings:
                # Deleting one card can fan out to N when the vfolder is shared
                # -- surface that for ops/debugging since the caller only asked
                # for a single id.
                log.debug(
                    "model card delete: cascaded {} sibling card(s) on vfolder {} "
                    "alongside target {}",
                    len(siblings),
                    vfolder_id,
                    deleted.id,
                )
            await w.update_data(VFolderSoftDeleteUpdater(vfolder_id=vfolder_id))
        return deleted.id

    async def _reject_if_vfolder_mounted(self, w: V2WriteOps, vfolder_id: VFolderUUID) -> None:
        """Raise :class:`VFolderDeletionNotAllowed` if the VFolder is mounted on a live session.

        Matches the rejection :meth:`VFolderRepository.move_vfolders_to_trash` reports.
        """
        vfolder = await w.query_data(VFolderQuerier(vfolder_id=vfolder_id))
        if vfolder is None:
            return
        mounted = await w.search_in_global(
            LiveSessionsMountingVFolderSearcher(
                pagination=NoPagination(),
                vfolder_id=VFolderID(vfolder.quota_scope_id, vfolder.id),
            )
        )
        if mounted.items:
            session_ids = [str(session_id) for session_id in mounted.items]
            raise VFolderDeletionNotAllowed(
                "Cannot delete the vfolder. "
                f"The vfolder(id: {vfolder_id}) is mounted on sessions(ids: {session_ids})."
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
        async with self._v2_ops.read_ops() as r:
            result = await r.search_in_global(
                DeploymentPresetSearcher(
                    pagination=OffsetPagination(
                        limit=search_input.limit or 20, offset=search_input.offset or 0
                    ),
                    conditions=[
                        DeploymentRevisionPresetConditions.satisfying_model_card(
                            ModelCardID(model_card_id)
                        )
                    ],
                )
            )
        return AvailablePresetsSearchResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_scan_target_vfolders(self, project_id: UUID) -> list[VFolderScanData]:
        async with self._v2_ops.read_ops() as r:
            project = await r.query_data(ProjectQuerier(project_id=ProjectID(project_id)))
            if project is None:
                raise ProjectNotFound(str(project_id))
            if project.type != ProjectType.MODEL_STORE:
                raise InvalidProjectTypeForModelCard(
                    extra_msg=f"Project {project_id} is type '{project.type}', expected 'model-store'"
                )
            result = await r.search_in_global(
                VFolderScanTargetSearcher(
                    pagination=NoPagination(),
                    conditions=[
                        lambda: sa.and_(
                            VFolderRow.group == project_id,
                            VFolderRow.usage_mode == VFolderUsageMode.MODEL,
                            VFolderRow.status.not_in(DEAD_VFOLDER_STATUSES),
                        )
                    ],
                    project_id=ProjectID(project_id),
                )
            )
            return result.items

    async def get_existing_card_names(self, project_id: UUID, domain: str) -> set[str]:
        async with self._v2_ops.read_ops() as r:
            result = await r.search_in_global(
                ModelCardSearcher(
                    pagination=NoPagination(),
                    conditions=[
                        lambda: sa.and_(
                            ModelCardRow.project == project_id,
                            ModelCardRow.domain == domain,
                        )
                    ],
                )
            )
            return {card.name for card in result.items}

    async def bulk_upsert_scan(
        self,
        specs: Sequence[ModelCardScanUpserter],
        existing_names: set[str],
    ) -> tuple[int, int]:
        """Register every scanned card and its requirement rows; (created, updated).

        The upsert also provisions each card in the RBAC graph and enrolls it in its
        project, idempotently. The requirement rows are replaced per card, so a
        re-scan of the same input leaves the row count unchanged.
        """
        if not specs:
            return 0, 0
        async with self._v2_ops.write_ops() as w:
            cards = await w.atomic_upsert_entities(list(specs))
            for spec, card in zip(specs, cards, strict=True):
                await self._replace_min_resource(w, ModelCardID(card.id), spec.min_resource)
        updated = sum(1 for spec in specs if spec.name in existing_names)
        return len(specs) - updated, updated
