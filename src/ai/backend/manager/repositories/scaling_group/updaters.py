"""UpdaterSpec implementations for scaling group repository."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ScalingGroupStatusUpdaterSpec(UpdaterSpec[ScalingGroupRow]):
    """UpdaterSpec for scaling group status updates.

    Maps to ScalingGroupStatusGQL in GraphQL types.
    """

    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.is_active.update_dict(to_update, "is_active")
        self.is_public.update_dict(to_update, "is_public")
        return to_update


@dataclass
class ScalingGroupMetadataUpdaterSpec(UpdaterSpec[ScalingGroupRow]):
    """UpdaterSpec for scaling group metadata updates.

    Maps to ScalingGroupMetadataGQL in GraphQL types.
    Note: created_at is not updatable.
    """

    description: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.description.update_dict(to_update, "description")
        return to_update


@dataclass
class ScalingGroupNetworkConfigUpdaterSpec(UpdaterSpec[ScalingGroupRow]):
    """UpdaterSpec for scaling group network configuration updates.

    Maps to ScalingGroupNetworkConfigGQL in GraphQL types.
    """

    wsproxy_addr: TriState[str] = field(default_factory=TriState[str].nop)
    wsproxy_api_token: TriState[str] = field(default_factory=TriState[str].nop)
    use_host_network: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.wsproxy_addr.update_dict(to_update, "wsproxy_addr")
        self.wsproxy_api_token.update_dict(to_update, "wsproxy_api_token")
        self.use_host_network.update_dict(to_update, "use_host_network")
        return to_update


@dataclass
class ScalingGroupDriverConfigUpdaterSpec(UpdaterSpec[ScalingGroupRow]):
    """UpdaterSpec for scaling group driver configuration updates.

    Maps to ScalingGroupDriverConfigGQL in GraphQL types.
    """

    driver: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    driver_opts: OptionalState[Mapping[str, Any]] = field(
        default_factory=OptionalState[Mapping[str, Any]].nop
    )

    @property
    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.driver.update_dict(to_update, "driver")
        if (driver_opts := self.driver_opts.optional_value()) is not None:
            to_update["driver_opts"] = dict(driver_opts)
        return to_update


@dataclass
class ScalingGroupSchedulerConfigUpdaterSpec(UpdaterSpec[ScalingGroupRow]):
    """UpdaterSpec for scaling group scheduler configuration updates.

    Maps to ScalingGroupSchedulerConfigGQL in GraphQL types.
    """

    scheduler: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    scheduler_opts: OptionalState[ScalingGroupOpts] = field(
        default_factory=OptionalState[ScalingGroupOpts].nop
    )

    @property
    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.scheduler.update_dict(to_update, "scheduler")
        if (scheduler_opts := self.scheduler_opts.optional_value()) is not None:
            to_update["scheduler_opts"] = scheduler_opts
        return to_update


@dataclass
class ResourceGroupFairShareUpdaterSpec(UpdaterSpec[ScalingGroupRow]):
    """UpdaterSpec for scaling group fair share configuration updates.

    Maps to FairShareScalingGroupSpec in types.
    """

    fair_share_spec: TriState[FairShareScalingGroupSpec] = field(
        default_factory=TriState[FairShareScalingGroupSpec].nop
    )

    @property
    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.fair_share_spec.update_dict(to_update, "fair_share_spec")
        return to_update


@dataclass
class ScalingGroupUpdaterSpec(UpdaterSpec[ScalingGroupRow]):
    """Composite UpdaterSpec for scaling group updates.

    Combines status, metadata, network, driver, scheduler, and fair_share updates.
    Maps to ScalingGroupV2GQL structure in GraphQL types.
    """

    status: ScalingGroupStatusUpdaterSpec | None = None
    metadata: ScalingGroupMetadataUpdaterSpec | None = None
    network: ScalingGroupNetworkConfigUpdaterSpec | None = None
    driver: ScalingGroupDriverConfigUpdaterSpec | None = None
    scheduler: ScalingGroupSchedulerConfigUpdaterSpec | None = None
    fair_share: ResourceGroupFairShareUpdaterSpec | None = None

    @property
    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

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
