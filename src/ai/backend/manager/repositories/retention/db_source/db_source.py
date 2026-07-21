"""Database source for retention cleanup.

The single caller-facing operation is :meth:`sweep`: it reads every enabled
policy and drains records past each category's age boundary, stamping
``last_swept_at`` — all in one transaction. Categories map to purger specs via
one :meth:`_catalog`, and each spec drains via the shared ``batch_purge``.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.auth.login_session_types import LoginSessionStatus
from ai.backend.manager.data.deployment.types import ReplicaGroupLifecycle, RouteStatus
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
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.endpoint.row import EndpointRow, EndpointTokenRow
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.event_log.row import EventLogRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.resource_usage_history.row import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UsageBucketEntryRow,
    UserUsageBucketRow,
)
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
    BatchQuerier,
    NoPagination,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider, ReadOps, WriteOps
from ai.backend.manager.repositories.retention.purgers import RetentionPurgerSpec
from ai.backend.manager.repositories.retention.updaters import LastSweptAtUpdaterSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# usage_bucket_entries.bucket_type discriminators: the three bucket kinds share
# one FK-less entries table, so each parent purge matches its own entries.
_DOMAIN_BUCKET_TYPE = "domain"
_PROJECT_BUCKET_TYPE = "project"
_USER_BUCKET_TYPE = "user"


class RetentionDBSource:
    _ops: DBOpsProvider
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        ops_provider: DBOpsProvider,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._ops = ops_provider
        self._config_provider = config_provider

    @staticmethod
    def _catalog(
        threshold: datetime,
    ) -> Mapping[RetentionCategory, Sequence[RetentionPurgerSpec[Any]]]:
        """Build the ``category -> specs`` catalog with ``threshold`` bound.

        The ordered-delete categories (``sessions``, ``deployments``,
        ``usage_buckets``) list their specs child-before-parent so the drain
        removes FK-less or plain-FK children first. FK-CASCADE children are left
        to the DB unless they also need their own boundary sweep (terminal
        routings / replica_groups outliving a still-running endpoint).
        """
        # A session is held back while any kernel still references it or a
        # RESTRICT-guarded routing points at it, then purged once the blocker
        # ages out -- expressed as correlated NOT EXISTS guards.
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
                RetentionPurgerSpec(EventLogRow, EventLogRow.created_at, threshold),
                RetentionPurgerSpec(AuditLogRow, AuditLogRow.created_at, threshold),
                # error_logs purges purely on the boundary; is_read/is_cleared are ignored.
                RetentionPurgerSpec(ErrorLogRow, ErrorLogRow.created_at, threshold),
            ),
            # updated_at (not created_at): a retry merge touches updated_at, so a
            # recently-retried row keeps an old created_at but survives.
            RetentionCategory.RECONCILE_HISTORY: (
                RetentionPurgerSpec(
                    SessionSchedulingHistoryRow, SessionSchedulingHistoryRow.updated_at, threshold
                ),
                RetentionPurgerSpec(
                    KernelSchedulingHistoryRow, KernelSchedulingHistoryRow.updated_at, threshold
                ),
                RetentionPurgerSpec(
                    DeploymentHistoryRow, DeploymentHistoryRow.updated_at, threshold
                ),
                RetentionPurgerSpec(RouteHistoryRow, RouteHistoryRow.updated_at, threshold),
                RetentionPurgerSpec(
                    ReplicaGroupHistoryRow, ReplicaGroupHistoryRow.updated_at, threshold
                ),
            ),
            RetentionCategory.LOGIN: (
                RetentionPurgerSpec(LoginHistoryRow, LoginHistoryRow.created_at, threshold),
                RetentionPurgerSpec(
                    LoginSessionRow,
                    LoginSessionRow.invalidated_at,
                    threshold,
                    conditions=(
                        LoginSessionRow.status.in_((
                            LoginSessionStatus.INVALIDATED,
                            LoginSessionStatus.REVOKED,
                        )),
                    ),
                ),
            ),
            RetentionCategory.ROLES_INVITATIONS: (
                RetentionPurgerSpec(
                    RoleRow,
                    RoleRow.deleted_at,
                    threshold,
                    conditions=(RoleRow.status == RoleStatus.DELETED,),
                ),
                RetentionPurgerSpec(
                    RoleInvitationRow,
                    RoleInvitationRow.updated_at,
                    threshold,
                    conditions=(
                        RoleInvitationRow.state.in_(RoleInvitationState.declined_states()),
                    ),
                ),
                RetentionPurgerSpec(
                    VFolderInvitationRow,
                    VFolderInvitationRow.modified_at,
                    threshold,
                    conditions=(
                        VFolderInvitationRow.state.in_(VFolderInvitationState.declined_states()),
                    ),
                ),
            ),
            RetentionCategory.USAGE_RECORDS: (
                RetentionPurgerSpec(
                    KernelUsageRecordRow, KernelUsageRecordRow.period_end, threshold
                ),
            ),
            RetentionCategory.SESSIONS: (
                RetentionPurgerSpec(
                    KernelRow,
                    KernelRow.terminated_at,
                    threshold,
                    conditions=(KernelRow.status.in_(KernelStatus.terminal_statuses()),),
                ),
                RetentionPurgerSpec(
                    SessionRow,
                    SessionRow.terminated_at,
                    threshold,
                    conditions=(
                        SessionRow.status.in_(SessionStatus.terminal_statuses()),
                        ~session_has_kernel,
                        ~session_has_routing,
                    ),
                ),
            ),
            # deployment_revisions carry no ON DELETE to endpoints, so they are
            # drained first by endpoint id; policies / auto_scaling_rules cascade.
            # Terminal routings / replica_groups outlive a still-live endpoint, so
            # they get their own boundary sweep; endpoint_tokens expire on theirs.
            RetentionCategory.DEPLOYMENTS: (
                RetentionPurgerSpec(
                    DeploymentRevisionRow,
                    EndpointRow.destroyed_at,
                    threshold,
                    match_column=DeploymentRevisionRow.endpoint,
                    source_key=EndpointRow.id,
                    source_conditions=(EndpointRow.lifecycle_stage == EndpointLifecycle.DESTROYED,),
                ),
                RetentionPurgerSpec(
                    RoutingRow,
                    RoutingRow.updated_at,
                    threshold,
                    conditions=(RoutingRow.status.in_(RouteStatus.terminal_statuses()),),
                ),
                RetentionPurgerSpec(
                    ReplicaGroupRow,
                    ReplicaGroupRow.updated_at,
                    threshold,
                    conditions=(
                        ReplicaGroupRow.lifecycle.in_(ReplicaGroupLifecycle.terminal_statuses()),
                    ),
                ),
                RetentionPurgerSpec(
                    EndpointRow,
                    EndpointRow.destroyed_at,
                    threshold,
                    conditions=(EndpointRow.lifecycle_stage == EndpointLifecycle.DESTROYED,),
                ),
                RetentionPurgerSpec(EndpointTokenRow, EndpointTokenRow.expires_at, threshold),
            ),
            # Each bucket kind is purged on its own period_end, with its FK-less
            # usage_bucket_entries (keyed by bucket_id + bucket_type) drained first.
            RetentionCategory.USAGE_BUCKETS: (
                RetentionPurgerSpec(
                    UsageBucketEntryRow,
                    DomainUsageBucketRow.period_end,
                    threshold,
                    conditions=(UsageBucketEntryRow.bucket_type == _DOMAIN_BUCKET_TYPE,),
                    match_column=UsageBucketEntryRow.bucket_id,
                    source_key=DomainUsageBucketRow.id,
                ),
                RetentionPurgerSpec(
                    DomainUsageBucketRow, DomainUsageBucketRow.period_end, threshold
                ),
                RetentionPurgerSpec(
                    UsageBucketEntryRow,
                    ProjectUsageBucketRow.period_end,
                    threshold,
                    conditions=(UsageBucketEntryRow.bucket_type == _PROJECT_BUCKET_TYPE,),
                    match_column=UsageBucketEntryRow.bucket_id,
                    source_key=ProjectUsageBucketRow.id,
                ),
                RetentionPurgerSpec(
                    ProjectUsageBucketRow, ProjectUsageBucketRow.period_end, threshold
                ),
                RetentionPurgerSpec(
                    UsageBucketEntryRow,
                    UserUsageBucketRow.period_end,
                    threshold,
                    conditions=(UsageBucketEntryRow.bucket_type == _USER_BUCKET_TYPE,),
                    match_column=UsageBucketEntryRow.bucket_id,
                    source_key=UserUsageBucketRow.id,
                ),
                RetentionPurgerSpec(UserUsageBucketRow, UserUsageBucketRow.period_end, threshold),
            ),
        }

    def _purger_specs(
        self,
        category: RetentionCategory,
        threshold: datetime,
    ) -> Sequence[RetentionPurgerSpec[Any]]:
        """Look up the category's specs (each already bound to ``threshold``)."""
        specs = self._catalog(threshold).get(category)
        if specs is None:
            raise RetentionCategoryNotSupportedError(
                f"Retention category '{category.value}' has no cleanup wired in this repository."
            )
        return specs

    async def sweep(self) -> list[RetentionPurgeResult]:
        """Purge every enabled category once, each isolated by a savepoint.

        Reads ``batch_size`` / ``per_tick_budget`` from config at call time (so a
        config change takes effect on the next tick). The tick runs in one
        ``write_ops`` session sharing a single ``now`` snapshot, but each category
        drains and stamps ``last_swept_at`` inside its own savepoint: a category
        keeps the delete-and-stamp together (no delete-without-stamp drift) while a
        failing category rolls back only its own savepoint and is skipped, so one
        broken category no longer aborts the whole tick.

        Policies are visited least-recently-swept first. A category with no wired
        cleanup raises :class:`RetentionCategoryNotSupportedError`; the loop
        isolates that (a pure lookup, so the transaction stays valid) and skips it
        without a stamp so it is retried once wired. When ``per_tick_budget`` is
        set, once the tick's cumulative deletions reach it the remaining
        categories are deferred to the next tick.
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
                try:
                    async with w.savepoint() as sp:
                        deleted = await self._drain_specs(sp, specs, batch_size)
                        await sp.update(
                            Updater(spec=LastSweptAtUpdaterSpec(now), pk_value=policy.id)
                        )
                except Exception:
                    log.exception(
                        "retention sweep failed for category {}; isolated and skipped",
                        policy.category.value,
                    )
                    continue
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
        specs: Sequence[RetentionPurgerSpec[Any]],
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
