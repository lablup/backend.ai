"""Update specs for the scaling_groups table."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy import cast, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import array as pg_array
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.dto.manager.v2.resource_group.request import (
    KUBERNETES_RESOURCE_GROUP_DRIVER,
)
from ai.backend.manager.data.resource_group.types import (
    FairShareResourceGroupSpec,
    ResourceGroupData,
)
from ai.backend.manager.data.resource_group.types import PreemptionConfig as DataPreemptionConfig
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.compute_cluster import (
    ComputeClusterNotFound,
    InvalidResourceGroupDriverOptions,
    ResourceGroupDriverChangeConflict,
)
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import DefaultResourceGroupAlreadyExists
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.searchable_fields import (
    ResourceGroupSearchableFields,
)
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.types import OptionalState, TriState

DEFAULT_RESOURCE_GROUP_INDEX = "uq_scaling_groups_is_default"


@dataclass
class ResourceGroupUpdater(GuardedDataUpdater[ResourceGroupRow, ResourceGroupData]):
    """Edits a resource group's status, metadata, network, driver, scheduler and
    fair-share settings.

    A driver change is checked against the stored driver: a `kubernetes` group must name a
    registered compute cluster, and neither the driver nor the cluster changes while the
    group has live sessions.
    """

    resource_group_id: ResourceGroupID
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_default: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    wsproxy_addr: TriState[str] = field(default_factory=TriState[str].nop)
    wsproxy_api_token: TriState[str] = field(default_factory=TriState[str].nop)
    use_host_network: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    driver: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    driver_opts: OptionalState[Mapping[str, Any]] = field(
        default_factory=OptionalState[Mapping[str, Any]].nop
    )
    scheduler: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    scheduler_opts: OptionalState[ResourceGroupOpts] = field(
        default_factory=OptionalState[ResourceGroupOpts].nop
    )
    preemption_config: OptionalState[DataPreemptionConfig] = field(
        default_factory=OptionalState[DataPreemptionConfig].nop
    )
    fair_share_spec: TriState[FairShareResourceGroupSpec] = field(
        default_factory=TriState[FairShareResourceGroupSpec].nop
    )

    @property
    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ResourceGroupRow.id

    @override
    def target_id_value(self) -> ResourceGroupID:
        return self.resource_group_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        new_driver = self.driver.optional_value()
        new_opts = self.driver_opts.optional_value()
        if new_driver is None and new_opts is None:
            return ()
        stored_cluster = ResourceGroupRow.driver_opts["compute_cluster"].astext
        driver: sa.ColumnElement[Any] = (
            sa.literal(new_driver) if new_driver is not None else ResourceGroupRow.driver.expression
        )
        compute_cluster: sa.ColumnElement[Any] = stored_cluster
        new_cluster: Any = None
        if new_opts is not None:
            new_cluster = new_opts.get("compute_cluster")
            compute_cluster = sa.literal(new_cluster, sa.String)
        is_kubernetes = driver == KUBERNETES_RESOURCE_GROUP_DRIVER
        checks: list[GuardCheck] = []
        if new_driver is None and not (isinstance(new_cluster, str) and new_cluster.strip()):
            checks.append(
                GuardCheck(
                    condition=lambda: ResourceGroupRow.driver != KUBERNETES_RESOURCE_GROUP_DRIVER,
                    error=InvalidResourceGroupDriverOptions(
                        "driver_opts.compute_cluster must be a non-empty string"
                        " for a kubernetes resource group"
                    ),
                )
            )
        if new_driver is None or new_driver == KUBERNETES_RESOURCE_GROUP_DRIVER:
            checks.append(
                GuardCheck(
                    condition=lambda: sa.or_(
                        sa.not_(is_kubernetes),
                        sa.exists().where(ComputeClusterRow.name == compute_cluster),
                    ),
                    error=ComputeClusterNotFound(
                        f"compute cluster {new_cluster!r} is not registered"
                        if new_opts is not None
                        else "the stored compute cluster is not registered"
                    ),
                )
            )
        changes = sa.or_(
            driver.is_distinct_from(ResourceGroupRow.driver),
            sa.and_(is_kubernetes, compute_cluster.is_distinct_from(stored_cluster)),
        )
        live_sessions = sa.exists().where(
            SessionRow.scaling_group_name == ResourceGroupRow.name,
            SessionRow.status.not_in(SessionStatus.terminal_statuses()),
        )
        checks.append(
            GuardCheck(
                condition=lambda: sa.or_(sa.not_(changes), sa.not_(live_sessions)),
                error=ResourceGroupDriverChangeConflict(
                    f"Resource group {self.resource_group_id} has live sessions;"
                    " terminate them before changing its driver or compute cluster"
                ),
            )
        )
        return checks

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name=DEFAULT_RESOURCE_GROUP_INDEX,
                error=DefaultResourceGroupAlreadyExists(
                    "Another resource group is already the default, clear it first"
                ),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.is_active.update_dict(to_update, "is_active")
        self.is_public.update_dict(to_update, "is_public")
        self.is_default.update_dict(to_update, "is_default")
        self.description.update_dict(to_update, "description")
        self.wsproxy_addr.update_dict(to_update, "wsproxy_addr")
        self.wsproxy_api_token.update_dict(to_update, "wsproxy_api_token")
        self.use_host_network.update_dict(to_update, "use_host_network")
        self.driver.update_dict(to_update, "driver")
        if (driver_opts := self.driver_opts.optional_value()) is not None:
            to_update["driver_opts"] = dict(driver_opts)
        self.scheduler.update_dict(to_update, "scheduler")
        if (scheduler_opts := self.scheduler_opts.optional_value()) is not None:
            to_update["scheduler_opts"] = scheduler_opts
        if (preemption := self.preemption_config.optional_value()) is not None:
            preemption_dict = {
                "enabled": preemption.enabled,
                "preemptible_priority": preemption.preemptible_priority,
                "order": preemption.order.value,
                "mode": preemption.mode.value,
                "preemption_min_runtime": preemption.preemption_min_runtime.total_seconds(),
                "victim_scope": preemption.victim_scope.value,
            }
            to_update["scheduler_opts"] = func.jsonb_set(
                sa.literal_column("scheduler_opts"),
                pg_array(["preemption"]),
                cast(preemption_dict, JSONB),
            )
        self.fair_share_spec.update_dict(to_update, "fair_share_spec")
        return to_update

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        return ResourceGroupSearchableFields.own.to_data(row)
