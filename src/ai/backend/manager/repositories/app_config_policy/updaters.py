"""UpdaterSpec for AppConfigPolicy rows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec


@dataclass
class AppConfigPolicyUpdaterSpec(UpdaterSpec[AppConfigPolicyRow]):
    """UpdaterSpec for `app_config_policies`.

    Only `scope_sources` is mutable — `config_name` is immutable and
    therefore never appears in ``build_values()``.
    """

    scope_sources: Sequence[AppConfigScopeType]

    @property
    @override
    def row_class(self) -> type[AppConfigPolicyRow]:
        return AppConfigPolicyRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {"scope_sources": list(self.scope_sources)}
