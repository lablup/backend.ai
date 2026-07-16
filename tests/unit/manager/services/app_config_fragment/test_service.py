"""Tests for AppConfigFragmentService with mocked repositories."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkItemError,
    AppConfigFragmentBulkResult,
    AppConfigFragmentData,
    AppConfigFragmentScope,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    Updater,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_create import (
    AppConfigFragmentBulkCreateItem,
    BulkCreateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_update import (
    BulkUpdateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    DomainAppConfigFragmentTarget,
    ScopedSearchAppConfigFragmentAction,
    UserAppConfigFragmentTarget,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.service import AppConfigFragmentService
from ai.backend.manager.types import OptionalState

_USER_UUID = uuid.uuid4()
_USER_ID = str(_USER_UUID)
_DOMAIN_ID = str(uuid.uuid4())


@dataclass(frozen=True)
class _BulkCreateScopeCase:
    """A scope to bulk-create at, with the scope ref every item's creator must carry.

    ``expected_scope_ref`` is ``None`` for ``public``: it is GLOBAL — outside the RBAC scope
    hierarchy — so it binds to no scope.
    """

    scope_type: AppConfigScopeType
    scope_id: str
    expected_scope_ref: RBACElementRef | None


def _fragment(
    *,
    scope_type: AppConfigScopeType = AppConfigScopeType.USER,
    scope_id: str = _USER_ID,
    config_name: str = "theme",
) -> AppConfigFragmentData:
    now = datetime.now(UTC)
    return AppConfigFragmentData(
        id=AppConfigFragmentID(uuid.uuid4()),
        config_name=config_name,
        scope_type=scope_type,
        scope_id=scope_id,
        config={"k": "v"},
        created_at=now,
        updated_at=now,
    )


class TestAppConfigFragmentService:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigFragmentRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> AppConfigFragmentService:
        # The allow-list write-gate lives in the repository (atomic with the write); the
        # service only delegates. Gate pass/reject is covered by the repository tests.
        return AppConfigFragmentService(repository=mock_repository)

    # --- create ---

    async def test_create_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment()
        mock_repository.create = AsyncMock(return_value=fragment)
        spec = AppConfigFragmentCreatorSpec(
            config_name="theme",
            scope_type=AppConfigScopeType.USER,
            scope_id=_USER_ID,
            config={"k": "v"},
        )

        result = await service.create(CreateAppConfigFragmentAction(creator_spec=spec))

        assert result.fragment == fragment
        mock_repository.create.assert_called_once_with(spec)

    # --- get / search ---

    async def test_get(self, service: AppConfigFragmentService, mock_repository: MagicMock) -> None:
        fragment = _fragment()
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
        fragment = _fragment()
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

        assert result.data == [fragment]
        assert result.total_count == 1
        mock_repository.admin_search.assert_called_once_with(querier)

    async def test_scoped_search_builds_domain_and_user_scopes(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment(config_name="theme")
        mock_repository.scoped_search = AsyncMock(
            return_value=AppConfigFragmentSearchResult(
                items=[fragment],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        domain_id = DomainID(uuid.uuid4())

        result = await service.scoped_search(
            ScopedSearchAppConfigFragmentAction(
                items=[
                    DomainAppConfigFragmentTarget(domain_id=domain_id),
                    UserAppConfigFragmentTarget(user_id=UserID(_USER_UUID)),
                ],
                querier=querier,
            )
        )

        assert result.data == [fragment]
        # queried_refs preserve the scoped principals (domain, then user).
        assert [ref.element_id for ref in result.queried_refs] == [str(domain_id), _USER_ID]
        mock_repository.scoped_search.assert_called_once()
        called_querier, called_scopes = mock_repository.scoped_search.call_args.args
        assert called_querier is querier
        assert called_scopes[0].domain_id == domain_id
        assert called_scopes[1].user_id == _USER_UUID

    # --- update ---

    async def test_update_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        updated = _fragment()
        mock_repository.update = AsyncMock(return_value=updated)
        updater = Updater(
            spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
            pk_value=updated.id,
        )

        result = await service.update(UpdateAppConfigFragmentAction(updater=updater))

        assert result.fragment == updated
        mock_repository.update.assert_called_once_with(updater)

    # --- purge ---

    async def test_purge_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment()
        mock_repository.purge = AsyncMock(return_value=fragment)
        purger_spec = AppConfigFragmentPurgerSpec(fragment_id=fragment.id)

        result = await service.purge(PurgeAppConfigFragmentAction(purger_spec=purger_spec))

        assert result.fragment == fragment
        mock_repository.purge.assert_called_once_with(purger_spec)

    # --- bulk ---

    @pytest.mark.parametrize(
        "case",
        [
            _BulkCreateScopeCase(
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
                expected_scope_ref=RBACElementRef(RBACElementType.USER, _USER_ID),
            ),
            _BulkCreateScopeCase(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                expected_scope_ref=RBACElementRef(RBACElementType.DOMAIN, _DOMAIN_ID),
            ),
            _BulkCreateScopeCase(
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                expected_scope_ref=None,
            ),
        ],
        ids=lambda case: case.scope_type.value,
    )
    async def test_bulk_create_delegates_to_repository(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        case: _BulkCreateScopeCase,
    ) -> None:
        fragments = [_fragment(), _fragment()]
        mock_repository.bulk_create = AsyncMock(
            return_value=AppConfigFragmentBulkResult(succeeded=fragments, failed=[])
        )

        result = await service.bulk_create(
            BulkCreateAppConfigFragmentAction(
                scope=AppConfigFragmentScope(scope_type=case.scope_type, scope_id=case.scope_id),
                items=[AppConfigFragmentBulkCreateItem(config_name="theme", config={"k": "v"})],
            )
        )

        assert result.succeeded == fragments
        assert result.failed == []
        mock_repository.bulk_create.assert_called_once_with([
            RBACEntityCreator(
                spec=AppConfigFragmentCreatorSpec(
                    config_name="theme",
                    scope_type=case.scope_type,
                    scope_id=case.scope_id,
                    config={"k": "v"},
                ),
                element_type=RBACElementType.APP_CONFIG_FRAGMENT,
                scope_ref=case.expected_scope_ref,
            )
        ])

    async def test_bulk_update_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragments = [_fragment(), _fragment()]
        mock_repository.bulk_update = AsyncMock(
            return_value=AppConfigFragmentBulkResult(succeeded=fragments, failed=[])
        )
        updaters = [
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
                pk_value=fragments[0].id,
            )
        ]

        result = await service.bulk_update(BulkUpdateAppConfigFragmentAction(updaters=updaters))

        assert result.succeeded == fragments
        assert result.failed == []
        mock_repository.bulk_update.assert_called_once_with(updaters)

    async def test_bulk_purge_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragments = [_fragment(), _fragment()]
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
        # each fragment is purged through its RBAC purger, so its scope binding goes with it
        mock_repository.bulk_purge.assert_called_once_with([
            RBACEntityPurger(
                row_class=AppConfigFragmentRow,
                pk_value=spec.fragment_id,
                spec=spec,
            )
            for spec in purger_specs
        ])

    async def test_bulk_create_propagates_partial_failures(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        succeeded = [_fragment()]
        failed = [AppConfigFragmentBulkItemError(index=1, message="write not allowed")]
        mock_repository.bulk_create = AsyncMock(
            return_value=AppConfigFragmentBulkResult(succeeded=succeeded, failed=failed)
        )

        result = await service.bulk_create(
            BulkCreateAppConfigFragmentAction(
                scope=AppConfigFragmentScope(scope_type=AppConfigScopeType.USER, scope_id=_USER_ID),
                items=[
                    AppConfigFragmentBulkCreateItem(config_name="theme", config={"k": "v"}),
                    AppConfigFragmentBulkCreateItem(config_name="menu", config={"k": "v"}),
                ],
            )
        )

        assert result.succeeded == succeeded
        assert result.failed == failed


class TestCreateActionScope:
    """The create action acts at the fragment's own scope — not admin-only/global."""

    @pytest.mark.parametrize(
        ("scope_type", "scope_id", "expected_scope_type", "expected_scope_id"),
        [
            (AppConfigScopeType.PUBLIC, "public", ScopeType.GLOBAL, ""),
            (AppConfigScopeType.DOMAIN, "default", ScopeType.DOMAIN, "default"),
            (AppConfigScopeType.USER, _USER_ID, ScopeType.USER, _USER_ID),
        ],
    )
    def test_scope_follows_fragment_scope(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
        expected_scope_type: ScopeType,
        expected_scope_id: str,
    ) -> None:
        action = CreateAppConfigFragmentAction(
            creator_spec=AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=scope_type,
                scope_id=scope_id,
                config={"k": "v"},
            ),
        )
        assert action.scope_type() == expected_scope_type
        assert action.scope_id() == expected_scope_id
