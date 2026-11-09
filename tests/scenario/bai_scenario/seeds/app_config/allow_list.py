"""Write specs for an app config allow-list entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.data.app_config.types import (
    AppConfigAllowListData,
    AppConfigDefinitionData,
)
from ai.backend.manager.models.app_config_allow_list.creators import AppConfigAllowListCreator
from ai.backend.testutils.scenario_steps import Language, Says, in_language
from bai_scenario.seeds.seeder import Naming, TestSeedRowFrom, joined

SCOPE_NAMES = {
    AppConfigScopeType.PUBLIC: Says("공개", english="public"),
    AppConfigScopeType.DOMAIN: Says("도메인", english="domain"),
    AppConfigScopeType.USER: Says("사용자", english="user"),
}
"""레포트에서 스코프 종류를 가리키는 이름."""


@dataclass(frozen=True)
class TestSeedAllowListEntry(TestSeedRowFrom[AppConfigDefinitionData, AppConfigAllowListData]):
    """The entry opening the given definition's name to one scope kind.

    The row carries no name of its own; the seeder's name only tells the rows apart in
    the report. ``rank`` left out means the scope kind's default.
    """

    scope_type: AppConfigScopeType
    rank: int | None = None
    name_hint: str = "entry"

    @override
    def kind(self) -> str:
        return Says("허용 목록 항목", english="Allow-list entry")

    @override
    def detail(self) -> str:
        scope = SCOPE_NAMES[self.scope_type]
        scope_name = in_language(scope, Language.ENGLISH)
        opened = Says(
            f"{scope} 스코프에서 이 이름의 설정을 지정할 수 있습니다",
            english=f"the config of this name can be set in the {scope_name} scope",
        )
        if self.rank is None:
            rank = Says(
                "순위는 그 스코프 종류의 기본값", english="rank is the default of the scope kind"
            )
        else:
            rank = Says(f"순위 {self.rank}", english=f"rank {self.rank}")
        return joined([opened, rank])

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
