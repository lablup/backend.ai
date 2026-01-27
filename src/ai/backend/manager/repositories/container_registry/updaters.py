"""UpdaterSpec implementations for container registry repository."""

from __future__ import annotations

import builtins
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast, override

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.exception import ContainerRegistryGroupsAlreadyAssociated
from ai.backend.manager.errors.image import ContainerRegistryGroupsAssociationNotFound
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

if TYPE_CHECKING:
    pass


async def handle_allowed_groups_update(
    session: SASession,
    registry_id: uuid.UUID,
    allowed_group_updates: AllowedGroupsModel,
) -> None:
    """
    Handle adding/removing group associations for a container registry.

    Args:
        session: Database session
        registry_id: Container registry UUID
        allowed_group_updates: Groups to add or remove

    Raises:
        ContainerRegistryGroupsAlreadyAssociated: If groups are already associated
        ContainerRegistryGroupsAssociationNotFound: If trying to remove non-existing associations
    """
    if allowed_group_updates.add:
        insert_values = [
            {"registry_id": registry_id, "group_id": group_id}
            for group_id in allowed_group_updates.add
        ]

        try:
            insert_query = sa.insert(AssociationContainerRegistriesGroupsRow).values(insert_values)
            await session.execute(insert_query)
        except sa.exc.IntegrityError as e:
            raise ContainerRegistryGroupsAlreadyAssociated(
                f"Already associated groups for registry_id: {registry_id}, group_ids: {allowed_group_updates.add}"
            ) from e

    if allowed_group_updates.remove:
        delete_query = (
            sa.delete(AssociationContainerRegistriesGroupsRow)
            .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
            .where(
                AssociationContainerRegistriesGroupsRow.group_id.in_(allowed_group_updates.remove)
            )
        )
        result = await session.execute(delete_query)
        if cast(CursorResult, result).rowcount == 0:
            raise ContainerRegistryGroupsAssociationNotFound(
                f"Tried to remove non-existing associations for registry_id: {registry_id}, group_ids: {allowed_group_updates.remove}"
            )


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
    def row_class(self) -> builtins.type[ContainerRegistryRow]:  # type: ignore[name-defined]
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
