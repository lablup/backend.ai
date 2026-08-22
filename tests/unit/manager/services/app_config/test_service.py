"""Tests for AppConfigService (the merged AppConfig read) with a mocked ops repository."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.specs.searcher import SearcherResult
from ai.backend.manager.repositories.app_config_fragment.types import (
    PublicAppConfigFragmentOperationScope,
    VisibleAppConfigFragmentOperationScope,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.app_config.actions.search import (
    AnonymousSearchAppConfigsAction,
    SearchAppConfigsAction,
)
from ai.backend.manager.services.app_config.service import AppConfigService

_USER_ID = UserID(uuid.uuid4())
_DOMAIN_ID = DomainID(uuid.uuid4())
_NOW = datetime.now(UTC)

FragmentFactory = Callable[[str, dict[str, Any], EntityIdentifier | None], AppConfigFragmentData]


@pytest.fixture
def make_fragment() -> FragmentFactory:
    """Factory for an ``AppConfigFragmentData`` — the caller names the fragment's identity
    (``config_name``, ``config``, owner); only the id and timestamps (which the merge does
    not read) are filled in.
    """

    def _make(
        config_name: str,
        config: dict[str, Any],
        owner: EntityIdentifier | None,
    ) -> AppConfigFragmentData:
        return AppConfigFragmentData(
            id=AppConfigFragmentID(uuid.uuid4()),
            config_name=config_name,
            scope_id=owner,
            config=config,
            created_at=_NOW,
            updated_at=_NOW,
        )

    return _make


class TestAppConfigService:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=OpsRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> AppConfigService:
        return AppConfigService(mock_repository)

    @pytest.fixture
    def found(self, mock_repository: MagicMock) -> Callable[[list[AppConfigFragmentData]], None]:
        def _found(fragments: list[AppConfigFragmentData]) -> None:
            mock_repository.search_in_scopes = AsyncMock(
                return_value=SearcherResult(
                    items=fragments,
                    total_count=len(fragments),
                    has_next_page=False,
                    has_previous_page=False,
                )
            )

        return _found

    @pytest.fixture
    def deep_merge_fragments(
        self,
        make_fragment: FragmentFactory,
        found: Callable[[list[AppConfigFragmentData]], None],
    ) -> None:
        # Rank-ordered (low -> high), so the user fragment overrides on merge.
        found([
            make_fragment("theme", {"theme": "light", "lang": "en"}, None),
            make_fragment("theme", {"theme": "dark"}, _USER_ID),
        ])

    @pytest.fixture
    def list_replace_fragments(
        self,
        make_fragment: FragmentFactory,
        found: Callable[[list[AppConfigFragmentData]], None],
    ) -> None:
        # A higher-rank list overrides the lower one WHOLE; nested dicts still recurse.
        found([
            make_fragment(
                "ui", {"nav": ["home", "about", "contact"], "theme": {"light": True}}, None
            ),
            make_fragment("ui", {"nav": ["dashboard"], "theme": {"dark": True}}, _USER_ID),
        ])

    @pytest.fixture
    def no_fragments(self, found: Callable[[list[AppConfigFragmentData]], None]) -> None:
        found([])

    @pytest.fixture
    def two_name_fragments(
        self,
        make_fragment: FragmentFactory,
        found: Callable[[list[AppConfigFragmentData]], None],
    ) -> None:
        # Visible fragments for both names, (config_name, rank)-ordered.
        found([
            make_fragment("theme", {"theme": "light", "lang": "en"}, None),
            make_fragment("theme", {"theme": "dark"}, _USER_ID),
            make_fragment("menu", {"items": ["a"]}, None),
        ])

    @pytest.fixture
    def public_only_fragments(
        self,
        make_fragment: FragmentFactory,
        found: Callable[[list[AppConfigFragmentData]], None],
    ) -> None:
        found([make_fragment("theme", {"theme": "light", "lang": "en"}, None)])

    async def test_search_deep_merges_applicable_fragments(
        self,
        service: AppConfigService,
        deep_merge_fragments: None,
    ) -> None:
        result = await service.search_app_configs(
            SearchAppConfigsAction(config_names=["theme"], user_id=_USER_ID, domain_id=_DOMAIN_ID)
        )

        assert [c.config_name for c in result.app_configs] == ["theme"]
        assert result.app_configs[0].config == {"theme": "dark", "lang": "en"}

    async def test_search_scopes_the_query_to_the_injected_user(
        self,
        service: AppConfigService,
        mock_repository: MagicMock,
        deep_merge_fragments: None,
    ) -> None:
        # The acting user is the whole scope, so a caller cannot name someone else's config.
        action = SearchAppConfigsAction(
            config_names=["theme"], user_id=_USER_ID, domain_id=_DOMAIN_ID
        )
        await service.search_app_configs(action)

        scopes, _searcher = mock_repository.search_in_scopes.call_args.args
        assert scopes == (
            VisibleAppConfigFragmentOperationScope(user_id=_USER_ID, domain_id=_DOMAIN_ID),
        )
        assert [target.scope_id for target in action.scope_targets()] == [_USER_ID]

    async def test_search_replaces_lists_wholesale(
        self,
        service: AppConfigService,
        list_replace_fragments: None,
    ) -> None:
        result = await service.search_app_configs(
            SearchAppConfigsAction(config_names=["ui"], user_id=_USER_ID, domain_id=_DOMAIN_ID)
        )

        # The user's shorter nav list fully replaces public's — no trailing "about"/"contact".
        assert result.app_configs[0].config == {
            "nav": ["dashboard"],
            "theme": {"light": True, "dark": True},
        }

    async def test_search_groups_by_name_and_merges_each(
        self,
        service: AppConfigService,
        two_name_fragments: None,
    ) -> None:
        result = await service.search_app_configs(
            SearchAppConfigsAction(
                config_names=["theme", "menu"], user_id=_USER_ID, domain_id=_DOMAIN_ID
            )
        )

        # One AppConfigData per requested name, in request order.
        assert [c.config_name for c in result.app_configs] == ["theme", "menu"]
        assert result.app_configs[0].config == {"theme": "dark", "lang": "en"}
        assert result.app_configs[1].config == {"items": ["a"]}

    async def test_search_repeats_duplicate_config_names_in_output(
        self,
        service: AppConfigService,
        public_only_fragments: None,
    ) -> None:
        # A config_name repeated in the request must be repeated in the output — each
        # position is merged independently, never collapsed into a single entry.
        result = await service.search_app_configs(
            SearchAppConfigsAction(
                config_names=["theme", "theme"], user_id=_USER_ID, domain_id=_DOMAIN_ID
            )
        )

        assert [c.config_name for c in result.app_configs] == ["theme", "theme"]
        assert result.app_configs[0].config == {"theme": "light", "lang": "en"}
        assert result.app_configs[1].config == {"theme": "light", "lang": "en"}

    async def test_search_without_matching_fragments_returns_an_empty_merge(
        self,
        service: AppConfigService,
        no_fragments: None,
    ) -> None:
        # No contributing fragment is an empty merge, not a 404.
        result = await service.search_app_configs(
            SearchAppConfigsAction(config_names=["unknown"], user_id=_USER_ID, domain_id=_DOMAIN_ID)
        )

        assert [c.config_name for c in result.app_configs] == ["unknown"]
        assert result.app_configs[0].config == {}

    async def test_search_keeps_the_merged_names_alongside_an_absent_one(
        self,
        service: AppConfigService,
        two_name_fragments: None,
    ) -> None:
        # "unknown" contributes nothing, but that must not withhold the names that did merge.
        result = await service.search_app_configs(
            SearchAppConfigsAction(
                config_names=["theme", "menu", "unknown"],
                user_id=_USER_ID,
                domain_id=_DOMAIN_ID,
            )
        )

        assert [c.config_name for c in result.app_configs] == ["theme", "menu", "unknown"]
        assert result.app_configs[0].config == {"theme": "dark", "lang": "en"}
        assert result.app_configs[1].config == {"items": ["a"]}
        assert result.app_configs[2].config == {}

    async def test_anonymous_search_queries_public_fragments_only(
        self,
        service: AppConfigService,
        mock_repository: MagicMock,
        public_only_fragments: None,
    ) -> None:
        # Naming no principal is the pre-login read: only public fragments are queried,
        # and no scope answers for the access.
        result = await service.anonymous_search_app_configs(
            AnonymousSearchAppConfigsAction(config_names=["theme"])
        )

        scopes, _searcher = mock_repository.search_in_scopes.call_args.args
        assert scopes == (PublicAppConfigFragmentOperationScope(),)
        assert result.app_configs[0].config == {"theme": "light", "lang": "en"}
