"""CreatorSpec implementations for app config allow-list repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.app_config.types import AppConfigAccessLevel, AppConfigScopeType
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class AppConfigAllowListCreatorSpec(CreatorSpec[AppConfigAllowListRow]):
    """CreatorSpec for an app config allow-list entry.

    ``rank`` is the merge priority every fragment under the entry carries; when not
    given, it falls back to the scope type's default (public=100, domain=200,
    user=300), which orders the scopes so a user's own fragment wins the merge.
    ``read_access`` / ``write_access`` likewise fall back to the scope type's default
    policy (public: read=public/write=admin, domain: read=authenticated/write=admin,
    user: read=owner/write=owner) when not given.
    """

    config_name: str
    scope_type: AppConfigScopeType
    rank: int | None = None
    read_access: AppConfigAccessLevel | None = None
    write_access: AppConfigAccessLevel | None = None

    @override
    def build_row(self) -> AppConfigAllowListRow:
        rank = self.rank if self.rank is not None else self.scope_type.default_rank()
        read_access = (
            self.read_access
            if self.read_access is not None
            else self.scope_type.default_read_access()
        )
        write_access = (
            self.write_access
            if self.write_access is not None
            else self.scope_type.default_write_access()
        )
        return AppConfigAllowListRow(
            config_name=self.config_name,
            scope_type=self.scope_type,
            rank=rank,
            read_access=read_access,
            write_access=write_access,
        )
