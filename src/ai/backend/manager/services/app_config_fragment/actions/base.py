from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import ActionTarget, FieldData
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkItemError,
    AppConfigFragmentData,
)
from ai.backend.manager.data.permission.types import RBACElementRef


class AppConfigFragmentScopeAction(BaseScopeAction):
    """Base for scope-level app config fragment actions (create, search)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_FRAGMENT


class AppConfigFragmentScopeActionResult(BaseScopeActionResult):
    pass


class AppConfigFragmentSingleEntityAction(BaseSingleEntityAction):
    """Base for single-entity app config fragment actions (get, update, purge)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_FRAGMENT

    @override
    def field_data(self) -> FieldData | None:
        return None


class AppConfigFragmentSingleEntityActionResult(BaseSingleEntityActionResult):
    pass


@dataclass(frozen=True)
class AppConfigFragmentBulkTarget(ActionTarget):
    """One existing fragment touched by a bulk update / purge, exposed for per-entity RBAC."""

    fragment_id: AppConfigFragmentID

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG_FRAGMENT, element_id=str(self.fragment_id)
        )


class AppConfigFragmentBulkAction(BaseBulkAction[AppConfigFragmentBulkTarget]):
    """Base for bulk app config fragment mutations over existing fragments (update / purge).

    Bulk operations span many fragments (potentially across scopes), so there is no single
    entity id to report. Each concrete action exposes its per-item targets via ``targets()``
    so the bulk RBAC validator can authorize the batch per fragment.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_FRAGMENT

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class AppConfigFragmentBulkActionResult(BaseBulkActionResult):
    """Partial-success result of a bulk app config fragment mutation.

    ``succeeded`` are the affected fragments; ``failed`` are the rejected/failed items with
    their batch index and reason. ``element_refs`` covers the succeeded fragments only.
    """

    succeeded: list[AppConfigFragmentData]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(
                element_type=RBACElementType.APP_CONFIG_FRAGMENT, element_id=str(fragment.id)
            )
            for fragment in self.succeeded
        ]
