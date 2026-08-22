"""UpdaterSpec implementations for resource group repository."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy import cast, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import array as pg_array

from ai.backend.manager.data.resource_group.types import FairShareResourceGroupSpec
from ai.backend.manager.data.resource_group.types import PreemptionConfig as DataPreemptionConfig
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import DefaultResourceGroupAlreadyExists
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

DEFAULT_SCALING_GROUP_INDEX = "uq_scaling_groups_is_default"


@dataclass
class ResourceGroupStatusUpdaterSpec(UpdaterSpec[ResourceGroupRow]):
    """UpdaterSpec for resource group status updates.

    Maps to ScalingGroupStatusGQL in GraphQL types.
    """

    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_default: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.is_active.update_dict(to_update, "is_active")
        self.is_public.update_dict(to_update, "is_public")
        self.is_default.update_dict(to_update, "is_default")
        return to_update


@dataclass
class ResourceGroupMetadataUpdaterSpec(UpdaterSpec[ResourceGroupRow]):
    """UpdaterSpec for resource group metadata updates.

    Maps to ScalingGroupMetadataGQL in GraphQL types.
    Note: created_at is not updatable.
    """

    description: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.description.update_dict(to_update, "description")
        return to_update


@dataclass
class ResourceGroupNetworkConfigUpdaterSpec(UpdaterSpec[ResourceGroupRow]):
    """UpdaterSpec for resource group network configuration updates.

    Maps to ScalingGroupNetworkConfigGQL in GraphQL types.
    """

    wsproxy_addr: TriState[str] = field(default_factory=TriState[str].nop)
    wsproxy_api_token: TriState[str] = field(default_factory=TriState[str].nop)
    use_host_network: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.wsproxy_addr.update_dict(to_update, "wsproxy_addr")
        self.wsproxy_api_token.update_dict(to_update, "wsproxy_api_token")
        self.use_host_network.update_dict(to_update, "use_host_network")
        return to_update


@dataclass
class ResourceGroupDriverConfigUpdaterSpec(UpdaterSpec[ResourceGroupRow]):
    """UpdaterSpec for resource group driver configuration updates.

    Maps to ScalingGroupDriverConfigGQL in GraphQL types.
    """

    driver: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    driver_opts: OptionalState[Mapping[str, Any]] = field(
        default_factory=OptionalState[Mapping[str, Any]].nop
    )

    @property
    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.driver.update_dict(to_update, "driver")
        if (driver_opts := self.driver_opts.optional_value()) is not None:
            to_update["driver_opts"] = dict(driver_opts)
        return to_update


@dataclass
class ResourceGroupSchedulerConfigUpdaterSpec(UpdaterSpec[ResourceGroupRow]):
    """UpdaterSpec for resource group scheduler configuration updates.

    Maps to ScalingGroupSchedulerConfigGQL in GraphQL types.
    """

    scheduler: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    scheduler_opts: OptionalState[ResourceGroupOpts] = field(
        default_factory=OptionalState[ResourceGroupOpts].nop
    )
    preemption_config: OptionalState[DataPreemptionConfig] = field(
        default_factory=OptionalState[DataPreemptionConfig].nop
    )

    @property
    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
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
        return to_update


@dataclass
class ResourceGroupFairShareUpdaterSpec(UpdaterSpec[ResourceGroupRow]):
    """UpdaterSpec for resource group fair share configuration updates.

    Maps to FairShareScalingGroupSpec in types.
    """

    fair_share_spec: TriState[FairShareResourceGroupSpec] = field(
        default_factory=TriState[FairShareResourceGroupSpec].nop
    )

    @property
    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.fair_share_spec.update_dict(to_update, "fair_share_spec")
        return to_update


@dataclass
class ResourceGroupUpdaterSpec(UpdaterSpec[ResourceGroupRow]):
    """Composite UpdaterSpec for resource group updates.

    Combines status, metadata, network, driver, scheduler, and fair_share updates.
    Maps to ScalingGroupV2GQL structure in GraphQL types.
    """

    status: ResourceGroupStatusUpdaterSpec | None = None
    metadata: ResourceGroupMetadataUpdaterSpec | None = None
    network: ResourceGroupNetworkConfigUpdaterSpec | None = None
    driver: ResourceGroupDriverConfigUpdaterSpec | None = None
    scheduler: ResourceGroupSchedulerConfigUpdaterSpec | None = None
    fair_share: ResourceGroupFairShareUpdaterSpec | None = None

    @property
    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name=DEFAULT_SCALING_GROUP_INDEX,
                error=DefaultResourceGroupAlreadyExists(
                    "Another resource group is already the default, clear it first"
                ),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        if self.status:
            to_update.update(self.status.build_values())
        if self.metadata:
            to_update.update(self.metadata.build_values())
        if self.network:
            to_update.update(self.network.build_values())
        if self.driver:
            to_update.update(self.driver.build_values())
        if self.scheduler:
            to_update.update(self.scheduler.build_values())
        if self.fair_share:
            to_update.update(self.fair_share.build_values())
        return to_update
