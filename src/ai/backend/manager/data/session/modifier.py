from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class SessionModifier(PartialModifier):
    """Modifier for session operations."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    image: OptionalState[str] = field(default_factory=OptionalState.nop)
    resource_slots: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    cluster_mode: OptionalState[str] = field(default_factory=OptionalState.nop)
    cluster_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    environ: TriState[dict[str, str]] = field(default_factory=TriState.nop)
    mounts: TriState[list[str]] = field(default_factory=TriState.nop)
    bootstrap_script: TriState[str] = field(default_factory=TriState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.image.update_dict(to_update, "image")
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.cluster_mode.update_dict(to_update, "cluster_mode")
        self.cluster_size.update_dict(to_update, "cluster_size")
        self.environ.update_dict(to_update, "environ")
        self.mounts.update_dict(to_update, "mounts")
        self.bootstrap_script.update_dict(to_update, "bootstrap_script")
        return to_update


@dataclass
class KernelModifier(PartialModifier):
    """Modifier for kernel operations."""

    cluster_role: OptionalState[str] = field(default_factory=OptionalState.nop)
    cluster_idx: OptionalState[int] = field(default_factory=OptionalState.nop)
    image: OptionalState[str] = field(default_factory=OptionalState.nop)
    resource_slots: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    local_rank: OptionalState[int] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.cluster_role.update_dict(to_update, "cluster_role")
        self.cluster_idx.update_dict(to_update, "cluster_idx")
        self.image.update_dict(to_update, "image")
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.local_rank.update_dict(to_update, "local_rank")
        return to_update
