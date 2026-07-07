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
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.types import VFolderID
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.kernel.row import DEAD_KERNEL_STATUSES, KernelRow
from ai.backend.manager.models.vfolder.row import VFolderRow, get_sessions_by_mounted_folder

__all__ = (
    "VFolderReferenceCheck",
    "VFolderReferenceHit",
    "VFOLDER_REFERENCE_CHECKS",
    "find_active_vfolder_references",
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
    query: Callable[[SASession, VFolderRow], Awaitable[Sequence[uuid.UUID]]]


@dataclass(frozen=True)
class VFolderReferenceHit:
    source: str
    describe: str
    referrer_ids: list[str]


async def _sessions_mounting(session: SASession, vfolder_row: VFolderRow) -> Sequence[uuid.UUID]:
    return list(await get_sessions_by_mounted_folder(session, VFolderID.from_row(vfolder_row)))


async def _kernels_mounting(session: SASession, vfolder_row: VFolderRow) -> Sequence[uuid.UUID]:
    stmt = sa.select(KernelRow.id).where(
        KernelRow.status.not_in(DEAD_KERNEL_STATUSES)
        & KernelRow.vfolder_mounts.contains([{"vfid": str(VFolderID.from_row(vfolder_row))}])
    )
    return list((await session.scalars(stmt)).all())


def _active_endpoint_ids_stmt(
    where_clause: sa.sql.expression.ColumnElement[bool],
) -> sa.Select[tuple[DeploymentID]]:
    return (
        sa.select(EndpointRow.id)
        .join(DeploymentRevisionRow, DeploymentRevisionRow.endpoint == EndpointRow.id)
        .where(EndpointRow.lifecycle_stage.in_(EndpointLifecycle.active_states()) & where_clause)
        .distinct()
    )


async def _active_endpoints_by_model(
    session: SASession, vfolder_row: VFolderRow
) -> Sequence[uuid.UUID]:
    stmt = _active_endpoint_ids_stmt(DeploymentRevisionRow.model == vfolder_row.id)
    return list((await session.scalars(stmt)).all())


async def _active_endpoints_by_extra_mount(
    session: SASession, vfolder_row: VFolderRow
) -> Sequence[uuid.UUID]:
    # ``extra_mounts`` stores ``MountInfoEntry.model_dump(mode="json")`` where
    # ``vfolder_id`` is the dashed UUID string (``str(uuid)``).
    stmt = _active_endpoint_ids_stmt(
        DeploymentRevisionRow.extra_mounts.contains([{"vfolder_id": str(vfolder_row.id)}])
    )
    return list((await session.scalars(stmt)).all())


# Order matters only for which reference is reported first in the error message.
VFOLDER_REFERENCE_CHECKS: list[VFolderReferenceCheck] = [
    VFolderReferenceCheck(
        source="sessions.vfolder_mounts",
        describe="mounted on live session(s)",
        query=_sessions_mounting,
    ),
    VFolderReferenceCheck(
        source="kernels.vfolder_mounts",
        describe="mounted on live kernel(s)",
        query=_kernels_mounting,
    ),
    VFolderReferenceCheck(
        source="deployment_revisions.model",
        describe="referenced as the model by active endpoint(s)",
        query=_active_endpoints_by_model,
    ),
    VFolderReferenceCheck(
        source="deployment_revisions.extra_mounts",
        describe="mounted as an extra mount by active endpoint(s)",
        query=_active_endpoints_by_extra_mount,
    ),
]


async def find_active_vfolder_references(
    session: SASession, vfolder_row: VFolderRow
) -> list[VFolderReferenceHit]:
    """Return every active reference to the vfolder across the registry.

    Empty when nothing actively references it (i.e. purge is safe w.r.t.
    in-use guards).
    """
    hits: list[VFolderReferenceHit] = []
    for check in VFOLDER_REFERENCE_CHECKS:
        referrer_ids = await check.query(session, vfolder_row)
        if referrer_ids:
            hits.append(
                VFolderReferenceHit(
                    source=check.source,
                    describe=check.describe,
                    referrer_ids=[str(rid) for rid in referrer_ids],
                )
            )
    return hits
