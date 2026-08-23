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
from ai.backend.manager.data.resource_group.types import (
    FairShareResourceGroupSpec,
    ResourceGroupData,
)
from ai.backend.manager.data.resource_group.types import PreemptionConfig as DataPreemptionConfig
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import DefaultResourceGroupAlreadyExists
from ai.backend.manager.models.resource_group.row import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState

DEFAULT_RESOURCE_GROUP_INDEX = "uq_scaling_groups_is_default"


@dataclass
class ResourceGroupUpdater(DataUpdater[ResourceGroupRow, ResourceGroupData]):
    """Edits a resource group's status, metadata, network, driver, scheduler and
    fair-share settings."""

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
        return row.to_dataclass()
