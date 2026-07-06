"""CreatorSpec implementations for app config allow-list repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base import CreatorSpec

# Default merge rank for a new allow-list entry when the caller does not pass one.
# Per-scope-type defaults are introduced in a follow-up; for now every scope shares
# this fixed rank.
DEFAULT_RANK = 100


@dataclass
class AppConfigAllowListCreatorSpec(CreatorSpec[AppConfigAllowListRow]):
    """CreatorSpec for an app config allow-list entry.

    ``rank`` is the merge priority every fragment under the entry carries; when not
    given, it falls back to ``DEFAULT_RANK``.
    """

    config_name: str
    scope_type: AppConfigScopeType
    rank: int | None = None

    @override
    def build_row(self) -> AppConfigAllowListRow:
        rank = self.rank if self.rank is not None else DEFAULT_RANK
        return AppConfigAllowListRow(
            config_name=self.config_name,
            scope_type=self.scope_type,
            rank=rank,
        )
