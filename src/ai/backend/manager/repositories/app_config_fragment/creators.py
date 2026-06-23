"""CreatorSpec implementations for app config fragment repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.data.app_config_fragment.types import AppConfigScopeType
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.creator import DependentCreatorSpec


@dataclass(frozen=True)
class AppConfigFragmentCreateDependency:
    """Execution-time values resolved while creating a fragment.

    Currently holds only the ``rank`` assigned by the ops layer (next-value). Kept as a
    dedicated type rather than a bare ``int`` so additional execution-resolved fields can
    be added later without changing ``build_row``'s signature.
    """

    rank: int


@dataclass
class AppConfigFragmentCreatorSpec(
    DependentCreatorSpec[AppConfigFragmentCreateDependency, AppConfigFragmentRow]
):
    """Fragment creator whose ``rank`` is assigned by the ops layer (next-value) at execution.

    ``build_row`` receives the resolved dependency, so a newly created fragment is placed
    after the existing fragments for the same ``config_name``.
    """

    config_name: str
    scope_type: AppConfigScopeType
    scope_id: str
    config: dict[str, Any]

    @override
    def build_row(self, dependency: AppConfigFragmentCreateDependency) -> AppConfigFragmentRow:
        return AppConfigFragmentRow(
            config_name=self.config_name,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            rank=dependency.rank,
            config=self.config,
        )
