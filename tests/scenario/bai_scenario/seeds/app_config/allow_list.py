"""Write specs for an app config allow-list entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRowFrom

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.data.app_config.types import (
    AppConfigAllowListData,
    AppConfigDefinitionData,
)
from ai.backend.manager.models.app_config_allow_list.creators import AppConfigAllowListCreator

SCOPE_NAMES = {
    AppConfigScopeType.PUBLIC: "공개",
    AppConfigScopeType.DOMAIN: "도메인",
    AppConfigScopeType.USER: "사용자",
}
"""스코프 종류를 레포트가 부르는 말."""


@dataclass(frozen=True)
class SeedAllowListEntry(SeedRowFrom[AppConfigDefinitionData, AppConfigAllowListData]):
    """The entry opening the given definition's name to one scope kind.

    The row carries no name of its own; the seeder's name only tells the rows apart in
    the report. ``rank`` left out means the scope kind's default.
    """

    scope_type: AppConfigScopeType
    rank: int | None = None
    name_hint: str = "entry"

    @override
    def kind(self) -> str:
        return "허용 항목"

    @override
    def detail(self) -> str:
        opened = f"{SCOPE_NAMES[self.scope_type]} 스코프가 이 이름을 채울 수 있다"
        if self.rank is None:
            return f"{opened}, 순위는 그 종류의 기본값"
        return f"{opened}, 순위 {self.rank}"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: AppConfigDefinitionData) -> AppConfigAllowListCreator:
        return AppConfigAllowListCreator(
            config_name=source.config_name,
            scope_type=self.scope_type,
            rank=self.rank,
        )
