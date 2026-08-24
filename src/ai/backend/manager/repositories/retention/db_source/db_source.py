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
from ai.backend.manager.models.error_log.row import ErrorLogRow
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
from ai.backend.manager.models.retention.searchers import RetentionPolicySearcher
from ai.backend.manager.models.retention.updaters import LastSweptAtUpdater
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.vfolder.row import VFolderInvitationRow
from ai.backend.manager.repositories.ops.v2.retention.provider import RetentionOpsProvider
from ai.backend.manager.repositories.ops.v2.retention.write import (
    RetentionDrain,
    RetentionWriteOps,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# usage_bucket_entries.bucket_type discriminators: the three bucket kinds share
# one FK-less entries table, so each parent purge matches its own entries.
_DOMAIN_BUCKET_TYPE = "domain"
_PROJECT_BUCKET_TYPE = "project"
_USER_BUCKET_TYPE = "user"


class RetentionDBSource:
    _ops: RetentionOpsProvider
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        ops_provider: RetentionOpsProvider,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._ops = ops_provider
        self._config_provider = config_provider

    @staticmethod
    def _catalog(
        threshold: datetime,
    ) -> Mapping[RetentionCategory, Sequence[RetentionDrain[Any]]]:
        """Build the ``category -> specs`` catalog with ``threshold`` bound.

        The ordered-delete categories (``sessions``, ``deployments``,
        ``usage_buckets``) list their specs child-before-parent so the drain
        removes FK-less or plain-FK children first. FK-CASCADE children are left
        to the DB unless they also need their own boundary sweep (terminal
        routings / replica_groups outliving a still-running endpoint). A parent
        that only becomes deletable once its referencing rows are gone
        (session_groups) is listed last instead.
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
        # A placement group outlives its owner replica group, so it is collected
        # once nothing references it any more.
        group_has_replica_group = (
            sa.select(sa.literal(1))
            .where(ReplicaGroupRow.session_group_id == SessionGroupRow.id)
            .correlate(SessionGroupRow)
            .exists()
        )
        return {
            RetentionCategory.LOGS: (
                RetentionDrain(EventLogRow, EventLogRow.created_at, threshold),
                RetentionDrain(AuditLogRow, AuditLogRow.created_at, threshold),
                # error_logs purges purely on the boundary; is_read/is_cleared are ignored.
                RetentionDrain(ErrorLogRow, ErrorLogRow.created_at, threshold),
            ),
            # updated_at (not created_at): a retry merge touches updated_at, so a
            # recently-retried row keeps an old created_at but survives.
            RetentionCategory.RECONCILE_HISTORY: (
                RetentionDrain(
                    SessionSchedulingHistoryRow, SessionSchedulingHistoryRow.updated_at, threshold
                ),
                RetentionDrain(
                    KernelSchedulingHistoryRow, KernelSchedulingHistoryRow.updated_at, threshold
                ),
                RetentionDrain(DeploymentHistoryRow, DeploymentHistoryRow.updated_at, threshold),
                RetentionDrain(RouteHistoryRow, RouteHistoryRow.updated_at, threshold),
                RetentionDrain(
                    ReplicaGroupHistoryRow, ReplicaGroupHistoryRow.updated_at, threshold
                ),
            ),
            RetentionCategory.LOGIN: (
                RetentionDrain(LoginHistoryRow, LoginHistoryRow.created_at, threshold),
                RetentionDrain(
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
                RetentionDrain(
                    RoleRow,
                    RoleRow.deleted_at,
                    threshold,
                    conditions=(RoleRow.status == RoleStatus.DELETED,),
                ),
                RetentionDrain(
                    RoleInvitationRow,
                    RoleInvitationRow.updated_at,
                    threshold,
                    conditions=(
                        RoleInvitationRow.state.in_(RoleInvitationState.declined_states()),
                    ),
                ),
                RetentionDrain(
                    VFolderInvitationRow,
                    VFolderInvitationRow.updated_at,
                    threshold,
                    conditions=(
                        VFolderInvitationRow.state.in_(VFolderInvitationState.declined_states()),
                    ),
                ),
            ),
            RetentionCategory.USAGE_RECORDS: (
                RetentionDrain(KernelUsageRecordRow, KernelUsageRecordRow.period_end, threshold),
            ),
            RetentionCategory.SESSIONS: (
                RetentionDrain(
                    KernelRow,
                    KernelRow.terminated_at,
                    threshold,
                    conditions=(KernelRow.status.in_(KernelStatus.terminal_statuses()),),
                ),
                RetentionDrain(
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
                RetentionDrain(
                    DeploymentRevisionRow,
                    EndpointRow.destroyed_at,
                    threshold,
                    match_column=DeploymentRevisionRow.endpoint,
                    source_key=EndpointRow.id,
                    source_conditions=(EndpointRow.lifecycle_stage == EndpointLifecycle.DESTROYED,),
                ),
                RetentionDrain(
                    RoutingRow,
                    RoutingRow.updated_at,
                    threshold,
                    conditions=(RoutingRow.status.in_(RouteStatus.terminal_statuses()),),
                ),
                RetentionDrain(
                    ReplicaGroupRow,
                    ReplicaGroupRow.updated_at,
                    threshold,
                    conditions=(
                        ReplicaGroupRow.lifecycle.in_(ReplicaGroupLifecycle.terminal_statuses()),
                    ),
                ),
                RetentionDrain(
                    EndpointRow,
                    EndpointRow.destroyed_at,
                    threshold,
                    conditions=(EndpointRow.lifecycle_stage == EndpointLifecycle.DESTROYED,),
                ),
                RetentionDrain(EndpointTokenRow, EndpointTokenRow.expires_at, threshold),
                # session_groups is the parent side of
                # replica_groups.session_group_id (NO ACTION, non-deferrable): a
                # group is deletable only once nothing references it, hence the
                # unreferenced guard instead of matching the terminal replica
                # groups, which would abort the statement. Ordering it last is
                # what collects the groups freed by the ReplicaGroupRow and
                # EndpointRow specs (the latter through the endpoint's cascade to
                # replica_groups) in the same tick rather than the next one.
                # Nothing else clears them: the application never hard-deletes a
                # replica group, and the FK points the wrong way for a DB cascade.
                RetentionDrain(
                    SessionGroupRow,
                    SessionGroupRow.created_at,
                    threshold,
                    conditions=(~group_has_replica_group,),
                ),
            ),
            # Each bucket kind is purged on its own period_end, with its FK-less
            # usage_bucket_entries (keyed by bucket_id + bucket_type) drained first.
            RetentionCategory.USAGE_BUCKETS: (
                RetentionDrain(
                    UsageBucketEntryRow,
                    DomainUsageBucketRow.period_end,
                    threshold,
                    conditions=(UsageBucketEntryRow.bucket_type == _DOMAIN_BUCKET_TYPE,),
                    match_column=UsageBucketEntryRow.bucket_id,
                    source_key=DomainUsageBucketRow.id,
                ),
                RetentionDrain(DomainUsageBucketRow, DomainUsageBucketRow.period_end, threshold),
                RetentionDrain(
                    UsageBucketEntryRow,
                    ProjectUsageBucketRow.period_end,
                    threshold,
                    conditions=(UsageBucketEntryRow.bucket_type == _PROJECT_BUCKET_TYPE,),
                    match_column=UsageBucketEntryRow.bucket_id,
                    source_key=ProjectUsageBucketRow.id,
                ),
                RetentionDrain(ProjectUsageBucketRow, ProjectUsageBucketRow.period_end, threshold),
                RetentionDrain(
                    UsageBucketEntryRow,
                    UserUsageBucketRow.period_end,
                    threshold,
                    conditions=(UsageBucketEntryRow.bucket_type == _USER_BUCKET_TYPE,),
                    match_column=UsageBucketEntryRow.bucket_id,
                    source_key=UserUsageBucketRow.id,
                ),
                RetentionDrain(UserUsageBucketRow, UserUsageBucketRow.period_end, threshold),
            ),
        }

    def _purger_specs(
        self,
        category: RetentionCategory,
        threshold: datetime,
    ) -> Sequence[RetentionDrain[Any]]:
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
                        await sp.update_data(
                            LastSweptAtUpdater(policy_id=policy.id, last_swept_at=now)
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

    async def _load_enabled_policies(self, r: RetentionWriteOps) -> list[RetentionPolicyData]:
        """Load every enabled policy, least-recently-swept first, on ``r``.

        The ordering makes the sweep fair under a per-tick budget: categories
        that have waited longest are drained before ones swept more recently.
        """
        result = await r.search_in_global(
            RetentionPolicySearcher(
                pagination=NoPagination(),
                conditions=[lambda: RetentionPolicyRow.enabled == sa.true()],
                orders=[RetentionPolicyRow.last_swept_at.asc().nulls_first()],
            )
        )
        return result.items

    async def _drain_specs(
        self,
        w: RetentionWriteOps,
        specs: Sequence[RetentionDrain[Any]],
        batch_size: int,
    ) -> int:
        """Drain each spec's rows on ``w`` in ``batch_size`` chunks; total deleted.

        Runs on the caller's session so the deletes join the caller's transaction
        (the sweep drains every category and stamps in one commit).
        """
        total_deleted = 0
        for spec in specs:
            total_deleted += await w.drain(spec, batch_size)
        return total_deleted
