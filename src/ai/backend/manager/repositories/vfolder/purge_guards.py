"""Registry of active vfolder references consulted by the purge in-use guard.

``vfolders.id`` is referenced in two forms:

- **Hard FK columns** — discoverable from the schema and (partly) enforced by
  the DB: ``model_cards.vfolder`` (RESTRICT), ``deployment_revisions.model``
  (SET NULL), and the ``vfolder_*`` CASCADE child tables.
- **Soft JSONB references** that embed a vfolder id but are *not* foreign keys,
  so schema metadata and the DB cannot see them:
  ``sessions.vfolder_mounts`` / ``kernels.vfolder_mounts`` (``VFolderMount``)
  and ``deployment_revisions.extra_mounts`` (``MountInfoEntry``).

The purge in-use guard must reject a purge while any *active* reference exists,
but the DB cannot enforce that for the soft references (and ``SET NULL`` FKs are
silently nulled rather than blocked). Both categories are therefore checked
explicitly through the registry below.

Each check carries one condition, read two ways: as a ``ConflictCheck`` the
purger spec declares (the delete runs only if no referrer exists), and as a
SELECT over ``referrer_id_column`` when the caller reports which rows blocked it.

TEMPORARY — the soft references should eventually be normalized into FK junction
tables; once that lands, the guard can enumerate FKs and this hand-maintained
list can shrink to the checks that need per-entity "active" semantics.
``tests/unit/manager/repositories/vfolder/test_vfolder_purge_guard_completeness.py``
introspects the ORM and fails if any ``VFolderMount`` / ``MountInfoEntry`` column
or non-CASCADE FK to ``vfolders.id`` is not represented here, so the list cannot
silently rot as the schema evolves.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import VFolderID
from ai.backend.manager.errors.storage import VFolderDeletionNotAllowed
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.kernel.row import DEAD_KERNEL_STATUSES, KernelRow
from ai.backend.manager.models.session.row import DEAD_SESSION_STATUSES, SessionRow
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.vfolder.row import VFolderRow

__all__ = (
    "VFolderReferenceCheck",
    "VFolderReferenceHit",
    "VFOLDER_REFERENCE_CHECKS",
    "find_active_vfolder_references",
    "vfolder_reference_conflict_checks",
)


@dataclass(frozen=True)
class VFolderReferenceCheck:
    """A single "is this vfolder actively referenced here?" probe.

    ``source`` is the ``"<table>.<column>"`` the reference lives in; the
    completeness test matches on it so every referencing column must appear as
    the ``source`` of exactly one check.
    """

    source: str
    describe: str
    referrer_id_column: InstrumentedAttribute[Any]
    build_condition: Callable[[VFolderID], sa.ColumnElement[bool]]

    def to_conflict_check(self, vfolder_id: VFolderID) -> ConflictCheck:
        condition = self.build_condition(vfolder_id)
        return ConflictCheck(
            condition=lambda: condition,
            error=VFolderDeletionNotAllowed(
                f"Cannot purge the vfolder(id: {vfolder_id.folder_id}); it is "
                f"{self.describe}. Remove the reference(s) first or set force=True."
            ),
        )


@dataclass(frozen=True)
class VFolderReferenceHit:
    source: str
    describe: str
    referrer_ids: list[str]


def _sessions_mounting(vfolder_id: VFolderID) -> sa.ColumnElement[bool]:
    return SessionRow.status.not_in(DEAD_SESSION_STATUSES) & SessionRow.vfolder_mounts.contains([
        {"vfid": str(vfolder_id)}
    ])


def _kernels_mounting(vfolder_id: VFolderID) -> sa.ColumnElement[bool]:
    return KernelRow.status.not_in(DEAD_KERNEL_STATUSES) & KernelRow.vfolder_mounts.contains([
        {"vfid": str(vfolder_id)}
    ])


def _active_endpoint_condition(
    where_clause: sa.ColumnElement[bool],
) -> sa.ColumnElement[bool]:
    return (
        EndpointRow.lifecycle_stage.in_(EndpointLifecycle.active_states())
        & (DeploymentRevisionRow.endpoint == EndpointRow.id)
        & where_clause
    )


def _active_endpoints_by_model(vfolder_id: VFolderID) -> sa.ColumnElement[bool]:
    return _active_endpoint_condition(DeploymentRevisionRow.model == vfolder_id.folder_id)


def _active_endpoints_by_extra_mount(vfolder_id: VFolderID) -> sa.ColumnElement[bool]:
    # ``extra_mounts`` stores ``MountInfoEntry.model_dump(mode="json")`` where
    # ``vfolder_id`` is the dashed UUID string (``str(uuid)``).
    return _active_endpoint_condition(
        DeploymentRevisionRow.extra_mounts.contains([{"vfolder_id": str(vfolder_id.folder_id)}])
    )


# Order matters only for which reference is reported first in the error message.
VFOLDER_REFERENCE_CHECKS: list[VFolderReferenceCheck] = [
    VFolderReferenceCheck(
        source="sessions.vfolder_mounts",
        describe="mounted on live session(s)",
        referrer_id_column=SessionRow.id,
        build_condition=_sessions_mounting,
    ),
    VFolderReferenceCheck(
        source="kernels.vfolder_mounts",
        describe="mounted on live kernel(s)",
        referrer_id_column=KernelRow.id,
        build_condition=_kernels_mounting,
    ),
    VFolderReferenceCheck(
        source="deployment_revisions.model",
        describe="referenced as the model by active endpoint(s)",
        referrer_id_column=EndpointRow.id,
        build_condition=_active_endpoints_by_model,
    ),
    VFolderReferenceCheck(
        source="deployment_revisions.extra_mounts",
        describe="mounted as an extra mount by active endpoint(s)",
        referrer_id_column=EndpointRow.id,
        build_condition=_active_endpoints_by_extra_mount,
    ),
]


def vfolder_reference_conflict_checks(vfolder_id: VFolderID) -> Sequence[ConflictCheck]:
    """The registry as conflict checks, for a purger spec to declare."""
    return tuple(check.to_conflict_check(vfolder_id) for check in VFOLDER_REFERENCE_CHECKS)


async def find_active_vfolder_references(
    session: SASession, vfolder_row: VFolderRow
) -> list[VFolderReferenceHit]:
    """Return every active reference to the vfolder across the registry.

    Empty when nothing actively references it (i.e. purge is safe w.r.t.
    in-use guards).
    """
    vfolder_id = VFolderID.from_row(vfolder_row)
    hits: list[VFolderReferenceHit] = []
    for check in VFOLDER_REFERENCE_CHECKS:
        stmt = (
            sa.select(check.referrer_id_column).where(check.build_condition(vfolder_id)).distinct()
        )
        referrer_ids: Sequence[uuid.UUID] = (await session.scalars(stmt)).all()
        if referrer_ids:
            hits.append(
                VFolderReferenceHit(
                    source=check.source,
                    describe=check.describe,
                    referrer_ids=[str(rid) for rid in referrer_ids],
                )
            )
    return hits
