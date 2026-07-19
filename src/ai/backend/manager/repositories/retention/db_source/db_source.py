"""Database source for retention cleanup.

Holds the ``category -> tables`` catalog (kept inside the repository, never a
module global) and drains each table with chunk-based delete-and-advance via
the shared ``batch_purge``.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.auth.login_session_types import LoginSessionStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.retention.types import RetentionCategory, RetentionPurgeResult
from ai.backend.manager.data.role_invitation.types import RoleInvitationState
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.vfolder.types import VFolderInvitationState
from ai.backend.manager.errors.retention import RetentionCategoryNotSupportedError
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.event_log.row import EventLogRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.resource_usage_history.row import KernelUsageRecordRow
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.vfolder.row import VFolderInvitationRow
from ai.backend.manager.repositories.base import BatchPurger, BatchPurgerSpec
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.retention.purgers import TimestampBoundaryPurgerSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Invitation states that are terminal (no further update expected), so their
# proxy timestamp is a safe grace boundary. Only PENDING is non-terminal.
_TERMINAL_ROLE_INVITATION_STATES = (
    RoleInvitationState.ACCEPTED,
    RoleInvitationState.REJECTED,
    RoleInvitationState.CANCELED,
)
_TERMINAL_VFOLDER_INVITATION_STATES = (
    VFolderInvitationState.ACCEPTED,
    VFolderInvitationState.REJECTED,
    VFolderInvitationState.CANCELED,
)


@dataclass(frozen=True)
class _BoundaryTable:
    """One table's fixed cleanup definition; only ``threshold`` varies per sweep.

    The boundary column is chosen by table nature: append-only logs use
    ``created_at``, in-place-merged history uses ``updated_at``, and lifecycle
    records use their terminal timestamp plus a terminal-status
    ``extra_conditions`` filter.
    """

    row_class: type[Base]
    boundary: Any
    extra_conditions: Sequence[ColumnElement[bool]] = field(default_factory=tuple)


class RetentionDBSource:
    _ops: DBOpsProvider
    _catalog: Mapping[RetentionCategory, Sequence[_BoundaryTable]]

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider
        self._catalog = self._build_catalog()

    @staticmethod
    def _build_catalog() -> Mapping[RetentionCategory, Sequence[_BoundaryTable]]:
        """Build the fixed ``category -> tables`` catalog once (column refs are
        constant; only the threshold is applied per sweep).

        ``deployments`` and ``usage_buckets`` keep a bespoke ordered delete and
        are intentionally absent until wired.
        """
        # sessions: kernels are listed before sessions so the ordered per-table
        # drain removes kernels first (kernels.session_id is a plain FK). A
        # session is skipped this sweep while any kernel still references it or a
        # RESTRICT-guarded routing points at it, then purged once the blocker
        # ages out -- expressed as correlated NOT EXISTS guards below.
        session_has_kernel = (
            sa.select(sa.literal(1))
            .where(KernelRow.session_id == SessionRow.id)
            .correlate(SessionRow)
            .exists()
        )
        session_has_routing = (
            sa.select(sa.literal(1))
            .where(RoutingRow.session == SessionRow.id)
            .correlate(SessionRow)
            .exists()
        )
        return {
            RetentionCategory.LOGS: (
                _BoundaryTable(EventLogRow, EventLogRow.created_at),
                _BoundaryTable(AuditLogRow, AuditLogRow.created_at),
                # error_logs purges purely on the boundary — is_read/is_cleared
                # flags are intentionally ignored (all rows past boundary go).
                _BoundaryTable(ErrorLogRow, ErrorLogRow.created_at),
            ),
            # updated_at (not created_at): attempts++ merges touch updated_at,
            # so a recently-retried row keeps an old created_at but survives.
            RetentionCategory.RECONCILE_HISTORY: (
                _BoundaryTable(SessionSchedulingHistoryRow, SessionSchedulingHistoryRow.updated_at),
                _BoundaryTable(KernelSchedulingHistoryRow, KernelSchedulingHistoryRow.updated_at),
                _BoundaryTable(DeploymentHistoryRow, DeploymentHistoryRow.updated_at),
                _BoundaryTable(RouteHistoryRow, RouteHistoryRow.updated_at),
                _BoundaryTable(ReplicaGroupHistoryRow, ReplicaGroupHistoryRow.updated_at),
            ),
            RetentionCategory.LOGIN: (
                _BoundaryTable(LoginHistoryRow, LoginHistoryRow.created_at),
                _BoundaryTable(
                    LoginSessionRow,
                    LoginSessionRow.invalidated_at,
                    (
                        LoginSessionRow.status.in_((
                            LoginSessionStatus.INVALIDATED,
                            LoginSessionStatus.REVOKED,
                        )),
                    ),
                ),
            ),
            RetentionCategory.ROLES_INVITATIONS: (
                _BoundaryTable(
                    RoleRow,
                    RoleRow.deleted_at,
                    (RoleRow.status == RoleStatus.DELETED,),
                ),
                _BoundaryTable(
                    RoleInvitationRow,
                    RoleInvitationRow.updated_at,
                    (RoleInvitationRow.state.in_(_TERMINAL_ROLE_INVITATION_STATES),),
                ),
                _BoundaryTable(
                    VFolderInvitationRow,
                    VFolderInvitationRow.modified_at,
                    (VFolderInvitationRow.state.in_(_TERMINAL_VFOLDER_INVITATION_STATES),),
                ),
            ),
            RetentionCategory.USAGE_RECORDS: (
                _BoundaryTable(KernelUsageRecordRow, KernelUsageRecordRow.period_end),
            ),
            RetentionCategory.SESSIONS: (
                _BoundaryTable(
                    KernelRow,
                    KernelRow.terminated_at,
                    (KernelRow.status.in_(KernelStatus.terminal_statuses()),),
                ),
                _BoundaryTable(
                    SessionRow,
                    SessionRow.terminated_at,
                    (
                        SessionRow.status.in_(SessionStatus.terminal_statuses()),
                        ~session_has_kernel,
                        ~session_has_routing,
                    ),
                ),
            ),
        }

    def _purger_specs(
        self,
        category: RetentionCategory,
        threshold: datetime,
    ) -> list[BatchPurgerSpec[Any]]:
        """Look up the category's tables and bind ``threshold`` into each spec."""
        tables = self._catalog.get(category)
        if tables is None:
            raise RetentionCategoryNotSupportedError(
                f"Retention category '{category.value}' has no simple/grouped "
                "cleanup wired in this repository."
            )
        return [
            TimestampBoundaryPurgerSpec(
                t.row_class, t.boundary, threshold, extra_conditions=t.extra_conditions
            )
            for t in tables
        ]

    async def purge_older_than(
        self,
        category: RetentionCategory,
        threshold: datetime,
        batch_size: int,
    ) -> RetentionPurgeResult:
        """Delete every row of ``category`` older than ``threshold``.

        Each of the category's tables is drained in its own transaction via
        ``batch_purge``, which deletes in ``batch_size`` chunks (delete-and-
        advance) so a large backlog never becomes a single huge DELETE.
        """
        specs = self._purger_specs(category, threshold)
        total_deleted = 0

        for spec in specs:
            async with self._ops.write_ops() as w:
                result = await w.batch_purge(BatchPurger(spec=spec, batch_size=batch_size))
                total_deleted += result.deleted_count

        log.debug(
            "retention purge category={} threshold={} deleted={}",
            category.value,
            threshold,
            total_deleted,
        )
        return RetentionPurgeResult(category=category, deleted_count=total_deleted)
