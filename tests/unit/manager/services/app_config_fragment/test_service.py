"""Tests for AppConfigFragmentService with mocked repositories."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkResult,
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.app_config_fragment.upserters import (
    AppConfigFragmentUpserterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.service import AppConfigFragmentService

_USER_ID = UserID(uuid.uuid4())
_DOMAIN_ID = DomainID(uuid.uuid4())

# The same owners seen as a fragment's scope_id, which is polymorphic over scope kinds.
_USER_SCOPE_ID = AppConfigScopeID(_USER_ID)
_DOMAIN_SCOPE_ID = AppConfigScopeID(_DOMAIN_ID)


@dataclass(frozen=True)
class _ScopedSearchCase:
    """One scope a scoped search runs at, and the RBAC scope id it reports."""

    scope: AppConfigFragmentSearchScope
    expected_rbac_scope_id: str


@pytest.fixture
def scoped_fragment() -> AppConfigFragmentData:
    """One fragment for the repository mock to return — the scope under test drives the case."""
    return AppConfigFragmentData(
        id=AppConfigFragmentID(uuid.uuid4()),
        config_name="theme",
        scope_type=AppConfigScopeType.USER,
        scope_id=_USER_SCOPE_ID,
        config={"k": "v"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@dataclass(frozen=True)
class _RBACScopeCase:
    """A fragment scope, and the RBAC scope a create at it authorizes against.

    RBAC identifies scopes by string, so the expected id is the rendered form — empty for
    public, which is global and names no owner.
    """

    scope_type: AppConfigScopeType
    scope_id: AppConfigScopeID | None
    expected_scope_type: ScopeType
    expected_scope_id: str


class TestAppConfigFragmentService:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigFragmentRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> AppConfigFragmentService:
        # The allow-list write-gate lives in the repository (atomic with the write); the
        # service only delegates. Gate pass/reject is covered by the repository tests.
        return AppConfigFragmentService(repository=mock_repository)

    # --- get / search ---

    async def test_get(self, service: AppConfigFragmentService, mock_repository: MagicMock) -> None:
        fragment = AppConfigFragmentData(
            id=AppConfigFragmentID(uuid.uuid4()),
            config_name="theme",
            scope_type=AppConfigScopeType.USER,
            scope_id=_USER_SCOPE_ID,
            config={"k": "v"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repository.get_by_id = AsyncMock(return_value=fragment)

        result = await service.get(GetAppConfigFragmentAction(fragment_id=fragment.id))

        assert result.fragment == fragment
        mock_repository.get_by_id.assert_called_once_with(fragment.id)

    async def test_get_not_found(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        missing_id = AppConfigFragmentID(uuid.uuid4())
        mock_repository.get_by_id = AsyncMock(
            side_effect=AppConfigFragmentNotFound(f"id {missing_id} not found")
        )

        with pytest.raises(AppConfigFragmentNotFound):
            await service.get(GetAppConfigFragmentAction(fragment_id=missing_id))

    async def test_admin_search(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = AppConfigFragmentData(
            id=AppConfigFragmentID(uuid.uuid4()),
            config_name="theme",
            scope_type=AppConfigScopeType.USER,
            scope_id=_USER_SCOPE_ID,
            config={"k": "v"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repository.admin_search = AsyncMock(
            return_value=AppConfigFragmentSearchResult(
                items=[fragment],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))

        result = await service.admin_search(AdminSearchAppConfigFragmentAction(querier=querier))

        assert result.items == [fragment]
        assert result.total_count == 1
        mock_repository.admin_search.assert_called_once_with(querier)

    @pytest.mark.parametrize(
        "case",
        [
            _ScopedSearchCase(
                scope=AppConfigFragmentSearchScope(
                    scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_SCOPE_ID
                ),
                expected_rbac_scope_id=str(_DOMAIN_SCOPE_ID),
            ),
            _ScopedSearchCase(
                scope=AppConfigFragmentSearchScope(
                    scope_type=AppConfigScopeType.USER, scope_id=_USER_SCOPE_ID
                ),
                expected_rbac_scope_id=str(_USER_SCOPE_ID),
            ),
        ],
        ids=lambda case: case.scope.scope_type.value,
    )
    async def test_scoped_search_passes_the_scope_through_to_the_repository(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        scoped_fragment: AppConfigFragmentData,
        case: _ScopedSearchCase,
    ) -> None:
        mock_repository.scoped_search = AsyncMock(
            return_value=AppConfigFragmentSearchResult(
                items=[scoped_fragment],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))

        result = await service.scoped_search(
            ScopedSearchAppConfigFragmentAction(scope=case.scope, querier=querier)
        )

        assert result.data == [scoped_fragment]
        # The result reports the RBAC scope the search was authorized at.
        assert result.scope_id() == case.expected_rbac_scope_id
        mock_repository.scoped_search.assert_called_once_with(querier, [case.scope])

    # --- purge ---

    async def test_purge_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = AppConfigFragmentData(
            id=AppConfigFragmentID(uuid.uuid4()),
            config_name="theme",
            scope_type=AppConfigScopeType.USER,
            scope_id=_USER_SCOPE_ID,
            config={"k": "v"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repository.purge = AsyncMock(return_value=fragment)
        purger_spec = AppConfigFragmentPurgerSpec(fragment_id=fragment.id)

        result = await service.purge(PurgeAppConfigFragmentAction(purger_spec=purger_spec))

        assert result.fragment == fragment
        mock_repository.purge.assert_called_once_with(purger_spec)

    # --- bulk ---

    async def test_bulk_purge_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragments = [
            AppConfigFragmentData(
                id=AppConfigFragmentID(uuid.uuid4()),
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                config={"k": "v"},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            for _ in range(2)
        ]
        mock_repository.bulk_purge = AsyncMock(
            return_value=AppConfigFragmentBulkResult(succeeded=fragments, failed=[])
        )
        purger_specs = [
            AppConfigFragmentPurgerSpec(fragment_id=fragments[0].id),
            AppConfigFragmentPurgerSpec(fragment_id=fragments[1].id),
        ]

        result = await service.bulk_purge(
            BulkPurgeAppConfigFragmentAction(purger_specs=purger_specs)
        )

        assert result.succeeded == fragments
        assert result.failed == []
        mock_repository.bulk_purge.assert_called_once_with(purger_specs)


class TestUpsertActionScope:
    """The upsert action acts at the scope it writes — not admin-only/global."""

    @pytest.mark.parametrize(
        "case",
        [
            _RBACScopeCase(
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id=None,
                expected_scope_type=ScopeType.GLOBAL,
                expected_scope_id="",
            ),
            _RBACScopeCase(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_SCOPE_ID,
                expected_scope_type=ScopeType.DOMAIN,
                expected_scope_id=str(_DOMAIN_ID),
            ),
            _RBACScopeCase(
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                expected_scope_type=ScopeType.USER,
                expected_scope_id=str(_USER_ID),
            ),
        ],
        ids=lambda case: case.scope_type.value,
    )
    def test_scope_follows_the_written_scope(self, case: _RBACScopeCase) -> None:
        action = BulkUpsertAppConfigFragmentsAction(
            scope=AppConfigFragmentSearchScope(scope_type=case.scope_type, scope_id=case.scope_id),
            upserter_specs=[
                AppConfigFragmentUpserterSpec(
                    config_name="theme",
                    scope_type=case.scope_type,
                    scope_id=case.scope_id,
                    config={"k": "v"},
                )
            ],
        )
        assert action.scope_type() == case.expected_scope_type
        assert action.scope_id() == case.expected_scope_id
