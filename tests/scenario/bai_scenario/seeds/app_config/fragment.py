"""Write specs for an app config fragment.

A fragment reads the allow-list entry rather than the definition: the row exists only
while an entry opens its name to its scope kind, so laying it on the entry writes the
entry first and makes the dependency visible in the report.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, override

from bai_scenario.seeds.seeder import Naming, SeedRowFrom, SeedRowFromTwo

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.app_config.types import (
    AppConfigAllowListData,
    AppConfigFragmentData,
)
from ai.backend.manager.models.app_config_fragment.upserters import (
    AppConfigFragmentUpserter,
    PublicAppConfigFragmentUpserter,
)


@dataclass(frozen=True)
class SeedFragmentOf[Owner](SeedRowFromTwo[AppConfigAllowListData, Owner, AppConfigFragmentData]):
    """The fragment the given owner holds under the given entry's name."""

    owner_of: Callable[[Owner], EntityIdentifier]
    config: Mapping[str, Any]
    name_hint: str = "fragment"

    @override
    def kind(self) -> str:
        return "설정 조각"

    @override
    def detail(self) -> str:
        return f"값 {dict(self.config)!r}"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self, name: str, first: AppConfigAllowListData, second: Owner
    ) -> AppConfigFragmentUpserter:
        return AppConfigFragmentUpserter(
            config_name=first.config_name,
            owner=self.owner_of(second),
            config=dict(self.config),
        )


@dataclass(frozen=True)
class SeedPublicFragment(SeedRowFrom[AppConfigAllowListData, AppConfigFragmentData]):
    """The public fragment under the given entry's name. It belongs to no one."""

    config: Mapping[str, Any]
    name_hint: str = "public-fragment"

    @override
    def kind(self) -> str:
        return "공개 설정 조각"

    @override
    def detail(self) -> str:
        return f"값 {dict(self.config)!r}"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: AppConfigAllowListData) -> PublicAppConfigFragmentUpserter:
        return PublicAppConfigFragmentUpserter(
            config_name=source.config_name, config=dict(self.config)
        )
