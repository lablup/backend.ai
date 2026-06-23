"""CreatorSpec implementations for app config definition repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import (
    GLOBAL_SCOPE_ID,
    EntityType,
    RelationType,
    ScopeType,
)
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base import CreatorSpec, DependentCreatorSpec


@dataclass
class AppConfigDefinitionCreatorSpec(CreatorSpec[AppConfigDefinitionRow]):
    """CreatorSpec for an app config definition."""

    config_name: str

    @override
    def build_row(self) -> AppConfigDefinitionRow:
        return AppConfigDefinitionRow(config_name=self.config_name)


@dataclass
class AppConfigDefinitionGlobalScopeAssociationSpec(
    DependentCreatorSpec[AppConfigDefinitionID, AssociationScopesEntitiesRow]
):
    """Registers a definition as an RBAC object at GLOBAL scope (BEP-1052, BA-6593).

    App config definitions are system-global, so the AUTO association is anchored at the
    GLOBAL scope. This makes object-level READ on ``(APP_CONFIG_DEFINITION, definition_id)``
    resolvable through the scope chain, which the AppConfigFragment scoped-search RBAC gate
    relies on.
    """

    @override
    def build_row(self, dependency: AppConfigDefinitionID) -> AssociationScopesEntitiesRow:
        return AssociationScopesEntitiesRow(
            scope_type=ScopeType.GLOBAL,
            scope_id=GLOBAL_SCOPE_ID,
            entity_type=EntityType.APP_CONFIG_DEFINITION,
            entity_id=str(dependency),
            relation_type=RelationType.AUTO,
        )
