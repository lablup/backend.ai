"""Tests for AppConfigService (merged AppConfig resolution) with a mocked repository."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.app_config.types import AppConfigAccessLevel, AppConfigScopeType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    VisibleFragment,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import AppConfigScopeArguments
from ai.backend.manager.services.app_config.actions.resolve import ResolveAppConfigAction
from ai.backend.manager.services.app_config.actions.resolve_bulk import (
    ResolveBulkAppConfigAction,
)
from ai.backend.manager.services.app_config.service import AppConfigService

_USER_ID = UserID(uuid.uuid4())
_DOMAIN_ID = DomainID(uuid.uuid4())
_NOW = datetime.now(UTC)
_SCOPE = AppConfigScopeArguments(domain_id=_DOMAIN_ID, user_id=_USER_ID)

# The caller behind _SCOPE: a regular user who owns the _USER_ID scope (satisfies the
# default read_access tiers — public, authenticated, and its own user layer).
_REQUESTER = UserData(
    user_id=_USER_ID,
    is_authorized=True,
    is_admin=False,
    is_superadmin=False,
    role=UserRole.USER,
    domain_name="default",
)
_SUPERADMIN = UserData(
    user_id=UserID(uuid.uuid4()),
    is_authorized=True,
    is_admin=True,
    is_superadmin=True,
    role=UserRole.SUPERADMIN,
    domain_name="default",
)

FragmentFactory = Callable[[str, dict[str, Any], AppConfigScopeType, str], AppConfigFragmentData]


def _visible(
    *fragments: AppConfigFragmentData,
    read_access: AppConfigAccessLevel | None = None,
) -> list[VisibleFragment]:
    """Wrap fragments as the read query now yields them — each paired with a ``read_access``
    tier (the scope-type default unless overridden), which the service filters against.
    """
    return [
        VisibleFragment(
            data=f,
            read_access=read_access
            if read_access is not None
            else f.scope_type.default_read_access(),
        )
        for f in fragments
    ]


@pytest.fixture
def make_fragment() -> FragmentFactory:
    """Factory for an ``AppConfigFragmentData`` — the caller names the fragment's identity
    (``config_name``, ``config``, ``scope_type``, ``scope_id``); only the id and timestamps
    (which the merge does not read) are filled in.
    """

    def _make(
        config_name: str,
        config: dict[str, Any],
        scope_type: AppConfigScopeType,
        scope_id: str,
    ) -> AppConfigFragmentData:
        return AppConfigFragmentData(
            id=AppConfigFragmentID(uuid.uuid4()),
            config_name=config_name,
            scope_type=scope_type,
            scope_id=scope_id,
            config=config,
            created_at=_NOW,
            updated_at=_NOW,
        )

    return _make


class TestAppConfigService:
    @pytest.fixture
    def mock_fragment_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigFragmentRepository)

    @pytest.fixture
    def service(self, mock_fragment_repository: MagicMock) -> AppConfigService:
        return AppConfigService(fragment_repository=mock_fragment_repository)

    async def test_resolve_deep_merges_applicable_fragments(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        make_fragment: FragmentFactory,
    ) -> None:
        # Fragments come rank-ordered (low -> high), so the later one overrides on merge.
        public = make_fragment(
            "theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, ""
        )
        user = make_fragment("theme", {"theme": "dark"}, AppConfigScopeType.USER, str(_USER_ID))
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(
            return_value=_visible(public, user)
        )

        result = await service.resolve_app_config(
            ResolveAppConfigAction(config_name="theme", scope=_SCOPE, requester=_REQUESTER)
        )

        assert result.app_config.config_name == "theme"
        assert result.app_config.fragments == [public, user]
        assert result.app_config.merged_config == {"theme": "dark", "lang": "en"}
        assert result.scope_id() == str(_USER_ID)
        mock_fragment_repository.list_visible_fragments_bulk.assert_called_once_with(
            ["theme"], _SCOPE
        )

    async def test_resolve_replaces_lists_wholesale(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        make_fragment: FragmentFactory,
    ) -> None:
        # A higher-rank list overrides the lower one WHOLE — not blended element-by-index.
        # Nested dicts still recurse (theme.light survives, theme.dark is added).
        public = make_fragment(
            "ui",
            {"nav": ["home", "about", "contact"], "theme": {"light": True}},
            AppConfigScopeType.PUBLIC,
            "",
        )
        user = make_fragment(
            "ui",
            {"nav": ["dashboard"], "theme": {"dark": True}},
            AppConfigScopeType.USER,
            str(_USER_ID),
        )
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(
            return_value=_visible(public, user)
        )

        result = await service.resolve_app_config(
            ResolveAppConfigAction(config_name="ui", scope=_SCOPE, requester=_REQUESTER)
        )

        # The user's shorter nav list fully replaces public's — no trailing "about"/"contact".
        assert result.app_config.merged_config == {
            "nav": ["dashboard"],
            "theme": {"light": True, "dark": True},
        }

    async def test_resolve_empty_yields_none_merged_config(
        self, service: AppConfigService, mock_fragment_repository: MagicMock
    ) -> None:
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(return_value=_visible())

        result = await service.resolve_app_config(
            ResolveAppConfigAction(config_name="unknown", scope=_SCOPE, requester=_REQUESTER)
        )

        # No contributing fragment -> None (unconfigured), not an empty {}.
        assert result.app_config.fragments == []
        assert result.app_config.merged_config is None

    async def test_resolve_bulk_groups_by_name_and_merges_each(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        make_fragment: FragmentFactory,
    ) -> None:
        # Repo returns visible fragments for both names, (config_name, rank)-ordered.
        theme_public = make_fragment(
            "theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, ""
        )
        theme_user = make_fragment(
            "theme", {"theme": "dark"}, AppConfigScopeType.USER, str(_USER_ID)
        )
        menu_public = make_fragment("menu", {"items": ["a"]}, AppConfigScopeType.PUBLIC, "")
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(
            return_value=_visible(theme_public, theme_user, menu_public)
        )

        result = await service.resolve_app_config_bulk(
            ResolveBulkAppConfigAction(
                config_names=["theme", "menu", "unknown"], scope=_SCOPE, requester=_REQUESTER
            )
        )

        # One AppConfigData per requested name, in request order.
        assert [c.config_name for c in result.app_configs] == ["theme", "menu", "unknown"]
        assert result.app_configs[0].merged_config == {"theme": "dark", "lang": "en"}
        assert result.app_configs[1].merged_config == {"items": ["a"]}
        assert result.app_configs[2].merged_config is None  # unregistered -> no fragments
        assert result.scope_id() == str(_USER_ID)
        mock_fragment_repository.list_visible_fragments_bulk.assert_called_once_with(
            ["theme", "menu", "unknown"], _SCOPE
        )

    async def test_resolve_bulk_repeats_duplicate_config_names_in_output(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        make_fragment: FragmentFactory,
    ) -> None:
        # A config_name repeated in the request must be repeated in the output — each
        # position resolves independently, never collapsed into a single entry.
        theme = make_fragment("theme", {"theme": "dark"}, AppConfigScopeType.PUBLIC, "")
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(
            return_value=_visible(theme)
        )

        result = await service.resolve_app_config_bulk(
            ResolveBulkAppConfigAction(
                config_names=["theme", "theme"], scope=_SCOPE, requester=_REQUESTER
            )
        )

        assert [c.config_name for c in result.app_configs] == ["theme", "theme"]
        assert result.app_configs[0].merged_config == {"theme": "dark"}
        assert result.app_configs[1].merged_config == {"theme": "dark"}

    async def test_resolve_without_scope_merges_public_fragments_only(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        make_fragment: FragmentFactory,
    ) -> None:
        # scope=None is the anonymous, pre-login read: only public fragments are queried,
        # and the result is attributable to no user.
        public = make_fragment(
            "theme", {"theme": "light", "lang": "en"}, AppConfigScopeType.PUBLIC, "public"
        )
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(
            return_value=_visible(public)
        )

        result = await service.resolve_app_config(ResolveAppConfigAction(config_name="theme"))

        assert result.app_config.config_name == "theme"
        assert result.app_config.fragments == [public]
        assert result.app_config.merged_config == {"theme": "light", "lang": "en"}
        assert result._user_id is None
        mock_fragment_repository.list_visible_fragments_bulk.assert_called_once_with(
            ["theme"], None
        )

    async def test_resolve_drops_layer_the_requester_cannot_read(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        make_fragment: FragmentFactory,
    ) -> None:
        # An admin has locked one layer to admin-only reads (non-default read_access): a
        # regular caller sees it in scope but must not read it — it is dropped before merge.
        public = make_fragment("theme", {"theme": "light"}, AppConfigScopeType.PUBLIC, "")
        locked = make_fragment("theme", {"theme": "secret"}, AppConfigScopeType.USER, str(_USER_ID))
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(
            return_value=_visible(public) + _visible(locked, read_access=AppConfigAccessLevel.ADMIN)
        )

        result = await service.resolve_app_config(
            ResolveAppConfigAction(config_name="theme", scope=_SCOPE, requester=_REQUESTER)
        )

        assert result.app_config.fragments == [public]
        assert result.app_config.merged_config == {"theme": "light"}

    async def test_resolve_superadmin_reads_every_layer(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        make_fragment: FragmentFactory,
    ) -> None:
        # A superadmin satisfies every tier, so an admin-locked layer still contributes.
        public = make_fragment("theme", {"theme": "light"}, AppConfigScopeType.PUBLIC, "")
        locked = make_fragment("theme", {"theme": "secret"}, AppConfigScopeType.USER, str(_USER_ID))
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(
            return_value=_visible(public) + _visible(locked, read_access=AppConfigAccessLevel.ADMIN)
        )

        result = await service.resolve_app_config(
            ResolveAppConfigAction(config_name="theme", scope=_SCOPE, requester=_SUPERADMIN)
        )

        assert result.app_config.fragments == [public, locked]
        assert result.app_config.merged_config == {"theme": "secret"}

    async def test_resolve_public_drops_non_public_readable_layer(
        self,
        service: AppConfigService,
        mock_fragment_repository: MagicMock,
        make_fragment: FragmentFactory,
    ) -> None:
        # Pre-login (requester=None): a layer whose read_access is above ``public`` — even a
        # public-scope fragment an admin raised to authenticated-only — is not readable.
        locked = make_fragment("theme", {"theme": "secret"}, AppConfigScopeType.PUBLIC, "")
        mock_fragment_repository.list_visible_fragments_bulk = AsyncMock(
            return_value=_visible(locked, read_access=AppConfigAccessLevel.AUTHENTICATED)
        )

        result = await service.resolve_app_config(ResolveAppConfigAction(config_name="theme"))

        assert result.app_config.fragments == []
        assert result.app_config.merged_config is None
