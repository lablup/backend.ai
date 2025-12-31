from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ScalingGroupUpdaterSpec(UpdaterSpec[ScalingGroupRow]):
    """UpdaterSpec for scaling group updates.

    Supports partial updates using OptionalState and TriState:
    - OptionalState: For non-nullable fields (update or no-op)
    - TriState: For nullable fields (update, nullify, or no-op)
    """

    # Nullable fields use TriState
    description: TriState[str] = field(default_factory=TriState[str].nop)
    wsproxy_addr: TriState[str] = field(default_factory=TriState[str].nop)
    wsproxy_api_token: TriState[str] = field(default_factory=TriState[str].nop)

    # Non-nullable fields use OptionalState
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    driver: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    driver_opts: OptionalState[Mapping[str, Any]] = field(
        default_factory=OptionalState[Mapping[str, Any]].nop
    )
    scheduler: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    scheduler_opts: OptionalState[ScalingGroupOpts] = field(
        default_factory=OptionalState[ScalingGroupOpts].nop
    )
    use_host_network: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}

        # Nullable fields (TriState)
        self.description.update_dict(to_update, "description")
        self.wsproxy_addr.update_dict(to_update, "wsproxy_addr")
        self.wsproxy_api_token.update_dict(to_update, "wsproxy_api_token")

        # Non-nullable fields (OptionalState)
        self.is_active.update_dict(to_update, "is_active")
        self.is_public.update_dict(to_update, "is_public")
        self.driver.update_dict(to_update, "driver")
        self.scheduler.update_dict(to_update, "scheduler")
        self.use_host_network.update_dict(to_update, "use_host_network")

        # Special handling for dict/object fields
        if (driver_opts := self.driver_opts.optional_value()) is not None:
            to_update["driver_opts"] = dict(driver_opts)
        if (scheduler_opts := self.scheduler_opts.optional_value()) is not None:
            to_update["scheduler_opts"] = scheduler_opts

        return to_update
