"""CreatorSpec implementations for app config fragment repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.creator import CreatorSpec

# Merge precedence by scope: lower ranks merge first, so a more specific scope (higher rank)
# overrides a broader one. Within one resolve there is at most one fragment per scope_type
# (unique on ``(config_name, scope_type, scope_id)``), so these ranks are distinct per merge.
_SCOPE_RANK: dict[AppConfigScopeType, int] = {
    AppConfigScopeType.PUBLIC: 100,
    AppConfigScopeType.DOMAIN: 200,
    AppConfigScopeType.USER: 300,
}


@dataclass
class AppConfigFragmentCreatorSpec(CreatorSpec[AppConfigFragmentRow]):
    """Fragment creator whose ``rank`` is derived from its ``scope_type`` (scope precedence).

    A fragment's rank is fixed by its scope (``public`` < ``domain`` < ``user``), so a more
    specific scope overrides a broader one when fragments are merged — independent of creation
    order. Being a plain ``CreatorSpec`` (rank known at build time), it composes with
    ``BulkConditionalCreator`` for gated bulk inserts.
    """

    config_name: str
    scope_type: AppConfigScopeType
    scope_id: str
    config: dict[str, Any]

    @override
    def build_row(self) -> AppConfigFragmentRow:
        return AppConfigFragmentRow(
            config_name=self.config_name,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            rank=_SCOPE_RANK[self.scope_type],
            config=self.config,
        )
