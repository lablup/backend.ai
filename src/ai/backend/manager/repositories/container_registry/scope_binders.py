"""RBAC scope binder/unbinder implementations for container registry."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)
from ai.backend.manager.repositories.container_registry.purgers import (
    ContainerRegistryGroupPurgerSpec,
)


@dataclass
class ContainerRegistryProjectEntityUnbinder(
    RBACScopeEntityUnbinder[AssociationContainerRegistriesGroupsRow],
):
    """Unbind a container registry from a project.

    Removes the N:N mapping row (AssociationContainerRegistriesGroupsRow)
    and the RBAC scope-entity association (Project -> ContainerRegistry).
    """

    registry_id: uuid.UUID
    group_id: uuid.UUID

    @override
    def build_purger_spec(
        self,
    ) -> BatchPurgerSpec[AssociationContainerRegistriesGroupsRow]:
        return ContainerRegistryGroupPurgerSpec(
            registry_id=self.registry_id,
            group_id=self.group_id,
        )

    @property
    @override
    def entity_type(self) -> RBACElementType:
        return RBACElementType.CONTAINER_REGISTRY

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.group_id))

    @property
    @override
    def entity_ids(self) -> Sequence[str] | None:
        return [str(self.registry_id)]
