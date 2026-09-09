"""Migrate the legacy etcd/keypair-policy idle checkers into DB-backed idle checkers.

Reads the legacy config through `manager.idle`'s own schema, so this command is retired
together with that module.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import click
import sqlalchemy as sa

from ai.backend.common import validators as tx
from ai.backend.common.data.idle_checker.types import (
    SESSION_ID_LABEL,
    CheckerType,
    IdleCheckerSpec,
    MetricLabel,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
    UtilizationSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    CONTAINER_UTILIZATION_METRIC_NAME,
)
from ai.backend.common.types import SessionTypes
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.cli.context import config_ctx
from ai.backend.manager.clients.prometheus.metric_types import DIFF_METRICS
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.idle import ThresholdOperator, UtilizationConfig
from ai.backend.manager.models.idle_checker.creators import (
    IdleCheckerAssignmentCreator,
    IdleCheckerCreator,
)
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerSearcher
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreator,
)
from ai.backend.manager.models.prometheus_query_preset.searchers import (
    PrometheusQueryPresetSearcher,
)
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.db.engine import connect_database
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# The agent exports only `current` and `capacity`, so the legacy `.pct` reading is rebuilt here.
_RATIO_PRESET_TEMPLATE = (
    f"avg by ({{group_by}})("
    f'{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}},value_type="current"}}}}'
    " / ignoring(value_type) "
    f'{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}},value_type="capacity"}}}}'
    ") * 100"
)
# `cpu_util` is a cumulative msec counter; 1000 msec/s is one core, i.e. 100%.
_RATE_PRESET_TEMPLATE = (
    f"avg by ({{group_by}})(rate("
    f'{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}},value_type="current"}}}}'
    f"[{{window}}])) / 1000 * 100"
)
# Wide enough that a missed 30s collection cycle cannot flatten the rate to zero.
_RATE_PRESET_TIME_WINDOW = "5m"

_DEFAULT_NETWORK_THRESHOLD = timedelta(minutes=10)


@dataclass(frozen=True)
class PlannedChecker:
    name: str
    description: str
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpec


@dataclass(frozen=True)
class UtilizationPlan:
    """Legacy utilization settings that have a representable equivalent."""

    window_seconds: int
    initial_grace_period_seconds: int
    thresholds: list[tuple[str, Decimal]]


@dataclass(frozen=True)
class LegacyKeypairPolicy:
    """One keypair resource policy's idle-related settings."""

    name: str
    max_session_lifetime: int
    idle_timeout: int


def plan_session_lifetime_checkers(
    policies: Sequence[LegacyKeypairPolicy],
) -> list[PlannedChecker]:
    """Plan one checker per distinct `max_session_lifetime`."""
    planned = []
    lifetimes = {policy.max_session_lifetime for policy in policies}
    # Exclude non-positive values, which mean "never expire" and have no representable spec.
    for seconds in sorted(lifetime_second for lifetime_second in lifetimes if lifetime_second > 0):
        planned.append(
            PlannedChecker(
                name=f"Legacy session lifetime ({seconds}s)",
                description=(
                    f"Migrated from keypair_resource_policies.max_session_lifetime ({seconds}s)."
                ),
                target_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
                initial_grace_period_seconds=0,
                spec=IdleCheckerSpec(
                    type=CheckerType.SESSION_LIFETIME,
                    session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=seconds),
                ),
            )
        )
    return planned


def plan_network_timeout_checkers(
    raw_checkers: Mapping[str, Any],
    policies: Sequence[LegacyKeypairPolicy],
) -> list[PlannedChecker]:
    """Plan one checker per distinct network idle threshold."""
    raw_threshold = (raw_checkers.get(CheckerType.NETWORK_TIMEOUT.value) or {}).get("threshold")
    parsed_threshold = tx.TimeDuration().check(raw_threshold) if raw_threshold else None
    # The legacy checker falls back on a falsy parse result, so a zero threshold runs the default.
    global_threshold = parsed_threshold or _DEFAULT_NETWORK_THRESHOLD
    candidates = {int(global_threshold.total_seconds())}
    # Exclude non-positive values, which mean "never expire" and have no representable spec.
    candidates |= {policy.idle_timeout for policy in policies if policy.idle_timeout > 0}
    planned = []
    for seconds in sorted(value for value in candidates if value > 0):
        planned.append(
            PlannedChecker(
                name=f"Legacy network timeout ({seconds}s)",
                description=f"Migrated from the legacy network_timeout checker ({seconds}s).",
                target_session_types=[SessionTypes.INTERACTIVE],
                initial_grace_period_seconds=0,
                spec=IdleCheckerSpec(
                    type=CheckerType.NETWORK_TIMEOUT,
                    network=NetworkTimeoutSpec(max_network_inactivity_seconds=seconds),
                ),
            )
        )
    return planned


def parse_utilization_config(
    raw_checkers: Mapping[str, Any],
    policies: Sequence[LegacyKeypairPolicy],
) -> UtilizationPlan | None:
    """Read the legacy utilization settings, warning about what cannot move.

    Returns ``None`` when the legacy checker could not have been running or has no
    representable threshold, so that no preset is created for a migration that yields
    no checker.
    """
    try:
        config = UtilizationConfig.model_validate(
            raw_checkers.get(CheckerType.UTILIZATION.value) or {}
        )
    except BackendAISchemaValidationFailed as e:
        log.warning(
            "utilization: the legacy config is invalid, so the checker could not have been "
            "running; nothing is migrated: {}",
            e,
        )
        return None
    if not isinstance(config.time_window, timedelta) or not isinstance(
        config.initial_grace_period, timedelta
    ):
        log.warning(
            "utilization: 'time-window' and 'initial-grace-period' must not use a 'yr' or 'mo' "
            "unit; nothing is migrated."
        )
        return None
    window_seconds = int(config.time_window.total_seconds())
    if window_seconds < 1:
        log.warning(
            "utilization: 'time-window' is non-positive, so the legacy checker could not have "
            "been running; nothing is migrated."
        )
        return None

    migratable: list[tuple[str, Decimal]] = []
    for resource, value in sorted(config.resource_thresholds.items()):
        if value.average is None:
            continue
        migratable.append((resource, Decimal(str(value.average))))

    if config.thresholds_check_operator is ThresholdOperator.AND and len(migratable) > 1:
        log.warning(
            "utilization: 'thresholds-check-operator: and' has no single-spec equivalent, so the "
            "{} generated checkers behave as OR and terminate MORE sessions than the legacy "
            "checker did.",
            len(migratable),
        )
    overridden = sorted(policy.name for policy in policies if policy.idle_timeout >= 0)
    if overridden:
        log.warning(
            "utilization: keypair resource policies {} override the utilization time window "
            "through their `idle_timeout`; that per-keypair override is not migrated.",
            overridden,
        )

    if not migratable:
        return None
    return UtilizationPlan(
        window_seconds=window_seconds,
        initial_grace_period_seconds=int(config.initial_grace_period.total_seconds()),
        thresholds=migratable,
    )


def plan_utilization_checkers(
    plan: UtilizationPlan,
    preset_ids: Mapping[str, PrometheusQueryPresetID],
) -> list[PlannedChecker]:
    """Plan one checker per parsed resource threshold."""
    window_seconds = plan.window_seconds
    planned = []
    for resource, threshold in plan.thresholds:
        planned.append(
            PlannedChecker(
                name=f"Legacy utilization ({resource} < {threshold}%)",
                description=(
                    f"Migrated from the legacy utilization checker ({resource} < {threshold}%, "
                    f"{window_seconds}s)."
                ),
                target_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
                initial_grace_period_seconds=plan.initial_grace_period_seconds,
                spec=IdleCheckerSpec(
                    type=CheckerType.UTILIZATION,
                    utilization=UtilizationSpec(
                        max_underutilized_duration_seconds=window_seconds,
                        threshold=UtilizationThresholdEntry(
                            preset_id=preset_ids[resource],
                            threshold=threshold,
                            filter_labels=[
                                MetricLabel(
                                    key=CONTAINER_UTILIZATION_METRIC_LABEL_NAME, value=resource
                                ),
                            ],
                            group_labels=[SESSION_ID_LABEL],
                        ),
                    ),
                ),
            )
        )
    return planned


async def _ensure_utilization_presets(
    ops_provider: V2DBOpsProvider,
    resources: Sequence[str],
) -> Mapping[str, PrometheusQueryPresetID]:
    """Map each resource to its preset, creating only the presets the resources need.

    Dedicated presets are used instead of seeded ones, because the seeded presets get
    renamed by later migrations and may have been edited by operators.
    """
    async with ops_provider.read_ops() as read_ops:
        presets = await read_ops.search_in_global(
            PrometheusQueryPresetSearcher(pagination=NoPagination())
        )
    known_ids = {preset.name: preset.id for preset in presets.items}
    preset_ids: dict[str, PrometheusQueryPresetID] = {}
    for resource in resources:
        if resource in DIFF_METRICS:
            name = "legacy:idle:container-utilization-rate"
            query_template = _RATE_PRESET_TEMPLATE
            time_window = _RATE_PRESET_TIME_WINDOW
            description = (
                "Per-session utilization percentage of a cumulative counter metric such as "
                "cpu_util, used by the idle checkers migrated from the legacy etcd configuration."
            )
        else:
            name = "legacy:idle:container-utilization-ratio"
            query_template = _RATIO_PRESET_TEMPLATE
            time_window = None
            description = (
                "Per-session utilization percentage rebuilt from the exported current and "
                "capacity values, used by the idle checkers migrated from the legacy etcd "
                "configuration."
            )
        preset_id = known_ids.get(name)
        if preset_id is None:
            async with ops_provider.write_ops() as write_ops:
                created = await write_ops.create_global_entity(
                    PrometheusQueryPresetCreator(
                        name=name,
                        metric_name=CONTAINER_UTILIZATION_METRIC_NAME,
                        query_template=query_template,
                        time_window=time_window,
                        filter_labels=[
                            CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
                            SESSION_ID_LABEL,
                        ],
                        group_labels=[SESSION_ID_LABEL],
                        description=description,
                    )
                )
            preset_id = created.id
            known_ids[name] = preset_id
            log.info("created prometheus query preset {}", name)
        preset_ids[resource] = preset_id
    return preset_ids


def _register_cli_orm_cluster() -> None:
    """Import the rows that string relationships on the reachable mappers refer to."""
    from ai.backend.manager.models.agent.row import AgentRow
    from ai.backend.manager.models.image.row import ImageRow
    from ai.backend.manager.models.prometheus_query_preset_category.row import (
        PrometheusQueryPresetCategoryRow,
    )
    from ai.backend.manager.models.rbac_models.association_scopes_entities import (
        AssociationScopesEntitiesRow,
    )
    from ai.backend.manager.models.resource_group.row import ResourceGroupForProjectRow

    _ = (
        AgentRow,
        ImageRow,
        PrometheusQueryPresetCategoryRow,
        AssociationScopesEntitiesRow,
        ResourceGroupForProjectRow,
    )


async def _migrate_legacy(cli_ctx: CLIContext) -> None:
    _register_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with config_ctx(cli_ctx) as unified_config:
        idle_config = unified_config.idle
    async with connect_database(bootstrap_config.db) as db:
        ops_provider = V2DBOpsProvider(db)
        relation_ops_provider = RelationOpsProvider(db)
        async with db.begin_readonly_session_read_committed() as db_sess:
            policy_query = sa.select(
                KeyPairResourcePolicyRow.name,
                KeyPairResourcePolicyRow.max_session_lifetime,
                KeyPairResourcePolicyRow.idle_timeout,
            )
            policies = [
                LegacyKeypairPolicy(
                    name=row.name,
                    max_session_lifetime=row.max_session_lifetime,
                    idle_timeout=row.idle_timeout,
                )
                for row in (await db_sess.execute(policy_query)).all()
            ]
            project_query = sa.select(ProjectRow.id).where(
                (ProjectRow.type == ProjectType.GENERAL) & ProjectRow.is_active.is_(True)
            )
            project_ids = [
                ProjectID(row.id) for row in (await db_sess.execute(project_query)).all()
            ]

        enabled = {name.strip() for name in idle_config.enabled.split(",")}
        planned_checkers = plan_session_lifetime_checkers(policies)
        if CheckerType.NETWORK_TIMEOUT.value in enabled:
            planned_checkers += plan_network_timeout_checkers(idle_config.checkers, policies)
        if CheckerType.UTILIZATION.value in enabled:
            utilization_plan = parse_utilization_config(idle_config.checkers, policies)
            if utilization_plan is not None:
                preset_ids = await _ensure_utilization_presets(
                    ops_provider, [resource for resource, _ in utilization_plan.thresholds]
                )
                planned_checkers += plan_utilization_checkers(utilization_plan, preset_ids)
        if not planned_checkers:
            log.info("No legacy idle checker setting to migrate.")
            return
        if not project_ids:
            log.warning("No project to bind the migrated checkers to.")

        # Re-runs match on what a checker *does*, so renaming or re-describing a migrated
        # checker afterwards does not make this command create a duplicate of it.
        async with ops_provider.read_ops() as read_ops:
            existing = await read_ops.search_in_global(
                IdleCheckerSearcher(pagination=NoPagination())
            )
        checker_ids = []
        for planned in planned_checkers:
            checker_id = None
            for checker in existing.items:
                if (
                    checker.spec == planned.spec
                    and list(checker.target_session_types) == planned.target_session_types
                    and checker.initial_grace_period_seconds == planned.initial_grace_period_seconds
                ):
                    checker_id = checker.id
                    break
            if checker_id is None:
                async with ops_provider.write_ops() as write_ops:
                    created = await write_ops.create_global_entity(
                        IdleCheckerCreator(
                            name=planned.name,
                            description=planned.description,
                            target_session_types=planned.target_session_types,
                            initial_grace_period_seconds=planned.initial_grace_period_seconds,
                            spec=planned.spec,
                        )
                    )
                checker_id = created.id
                log.info("created idle checker {}", planned.name)
            checker_ids.append(checker_id)

        # An already-bound pair is answered `False` rather than raised on, so re-running
        # only adds the bindings that are still missing.
        pairs = [
            (project_id, checker_id) for checker_id in checker_ids for project_id in project_ids
        ]
        created_assignments = 0
        if pairs:
            async with relation_ops_provider.write_ops() as relation_write_ops:
                written = await relation_write_ops.create_relations(
                    IdleCheckerAssignmentCreator(enabled=False), pairs
                )
            created_assignments = sum(written)
        log.info(
            "Migrated {} idle checker(s) and created {} disabled assignment(s) over {} project(s).",
            len(checker_ids),
            created_assignments,
            len(project_ids),
        )


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.pass_obj
def migrate_legacy(cli_ctx: CLIContext) -> None:
    """Build DB-backed idle checkers from the legacy etcd and keypair-policy settings.

    Every generated assignment is bound to a project and disabled, so running this changes
    no behavior; an admin enables the ones they want afterwards. Re-running only adds what
    is still missing.
    """
    asyncio.run(_migrate_legacy(cli_ctx))
