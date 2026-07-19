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
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.auth.login_session_types import LoginSessionStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.retention.types import (
    RetentionCategory,
    RetentionPolicyData,
    RetentionPurgeResult,
)
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
from ai.backend.manager.models.retention.row import RetentionPolicyRow
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
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchPurgerSpec,
    BatchQuerier,
    NoPagination,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider, ReadOps, WriteOps
from ai.backend.manager.repositories.retention.purgers import TimestampBoundaryPurgerSpec
from ai.backend.manager.repositories.retention.updaters import LastSweptAtUpdaterSpec

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
    _config_provider: ManagerConfigProvider
    _catalog: Mapping[RetentionCategory, Sequence[_BoundaryTable]]

    def __init__(
        self,
        ops_provider: DBOpsProvider,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._ops = ops_provider
        self._config_provider = config_provider
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

    async def sweep(self) -> list[RetentionPurgeResult]:
        """Purge every enabled category once, within a single transaction.

        Reads ``batch_size`` / ``per_tick_budget`` from config at call time (so a
        config change takes effect on the next tick). The whole sweep runs in one
        ``write_ops`` session, so reading DB ``now``, loading policies, draining
        each category, and stamping ``last_swept_at`` all share one snapshot and
        commit atomically at the end — a crash mid-tick rolls the entire tick
        back, leaving no delete-without-stamp drift.

        Policies are visited least-recently-swept first. A category whose cleanup
        is not wired yet (``deployments`` / ``usage_buckets``) raises
        :class:`RetentionCategoryNotSupportedError`; the loop isolates that (a
        pure lookup, so the transaction stays valid) and skips it without a stamp
        so it is retried once wired. When ``per_tick_budget`` is set, once the
        tick's cumulative deletions reach it the remaining categories are deferred
        to the next tick.
        """
        retention_config = self._config_provider.config.retention
        batch_size = retention_config.batch_size
        budget_remaining = retention_config.per_tick_budget
        results: list[RetentionPurgeResult] = []

        async with self._ops.write_ops() as w:
            now = await w.current_time()
            policies = await self._load_enabled_policies(w)

            for policy in policies:
                if budget_remaining is not None and budget_remaining <= 0:
                    log.debug(
                        "retention sweep per-tick budget exhausted; deferring remaining categories"
                    )
                    break
                threshold = now - policy.retention_period
                try:
                    specs = self._purger_specs(policy.category, threshold)
                except RetentionCategoryNotSupportedError:
                    log.debug(
                        "retention category {} has no cleanup wired yet; skipping",
                        policy.category.value,
                    )
                    continue
                deleted = await self._drain_specs(w, specs, batch_size)
                await w.update(Updater(spec=LastSweptAtUpdaterSpec(now), pk_value=policy.id))
                results.append(
                    RetentionPurgeResult(category=policy.category, deleted_count=deleted)
                )
                if budget_remaining is not None:
                    budget_remaining -= deleted

        total_deleted = sum(r.deleted_count for r in results)
        if total_deleted:
            log.info(
                "retention sweep deleted {} record(s) across {} categor(ies)",
                total_deleted,
                len(results),
            )
        return results

    async def _load_enabled_policies(self, r: ReadOps) -> list[RetentionPolicyData]:
        """Load every enabled policy, least-recently-swept first, on ``r``.

        The ordering makes the sweep fair under a per-tick budget: categories
        that have waited longest are drained before ones swept more recently.
        """
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[lambda: RetentionPolicyRow.enabled == sa.true()],
            orders=[RetentionPolicyRow.last_swept_at.asc().nulls_first()],
        )
        result = await r.batch_query_in_global(sa.select(RetentionPolicyRow), querier)
        return [row.RetentionPolicyRow.to_data() for row in result.rows]

    async def _drain_specs(
        self,
        w: WriteOps,
        specs: list[BatchPurgerSpec[Any]],
        batch_size: int,
    ) -> int:
        """Drain each spec's rows on ``w`` in ``batch_size`` chunks; total deleted.

        Runs on the caller's session so the deletes join the caller's transaction
        (the sweep drains every category and stamps in one commit).
        """
        total_deleted = 0
        for spec in specs:
            result = await w.batch_purge(BatchPurger(spec=spec, batch_size=batch_size))
            total_deleted += result.deleted_count
        return total_deleted
