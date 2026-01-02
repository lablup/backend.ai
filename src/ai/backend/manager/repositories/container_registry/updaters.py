"""UpdaterSpec implementations for container registry repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, override

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

if TYPE_CHECKING:
    import typing


@dataclass
class ContainerRegistryUpdaterSpec(UpdaterSpec[ContainerRegistryRow]):
    """UpdaterSpec for container registry updates."""

    url: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    type: OptionalState[ContainerRegistryType] = field(
        default_factory=OptionalState[ContainerRegistryType].nop
    )
    registry_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    is_global: TriState[bool] = field(default_factory=TriState[bool].nop)
    project: TriState[str] = field(default_factory=TriState[str].nop)
    username: TriState[str] = field(default_factory=TriState[str].nop)
    password: TriState[str] = field(default_factory=TriState[str].nop)
    ssl_verify: TriState[bool] = field(default_factory=TriState[bool].nop)
    extra: TriState[dict[str, Any]] = field(default_factory=TriState[dict[str, Any]].nop)
    allowed_groups: TriState[AllowedGroupsModel] = field(
        default_factory=TriState[AllowedGroupsModel].nop
    )

    @property
    def has_allowed_groups_update(self) -> bool:
        """Check if allowed_groups has updates to process."""
        groups = self.allowed_groups.optional_value()
        return groups is not None and (bool(groups.add) or bool(groups.remove))

    @property
    @override
    def row_class(self) -> typing.Type[ContainerRegistryRow]:  # type: ignore[name-defined]
        return ContainerRegistryRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.url.update_dict(to_update, "url")
        self.type.update_dict(to_update, "type")
        self.registry_name.update_dict(to_update, "registry_name")
        self.is_global.update_dict(to_update, "is_global")
        self.project.update_dict(to_update, "project")
        self.username.update_dict(to_update, "username")
        self.password.update_dict(to_update, "password")
        self.ssl_verify.update_dict(to_update, "ssl_verify")
        self.extra.update_dict(to_update, "extra")
        # Note: allowed_groups is handled separately in the repository method
        return to_update
