"""Tests for AppConfigFragmentService with mocked repositories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.app_config.types import AppConfigAccessLevel, AppConfigScopeType
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkItemError,
    AppConfigFragmentBulkResult,
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentNotFound,
    AppConfigFragmentWriteNotAllowed,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.app_config_allow_list.repository import (
    AppConfigAllowListRepository,
)
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    Creator,
    OffsetPagination,
    Purger,
    Updater,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_create import (
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
_OTHER_UUID = uuid.uuid4()


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


def _user(
    user_uuid: uuid.UUID = _USER_UUID,
    *,
    is_admin: bool = False,
    is_superadmin: bool = False,
    domain: str = "default",
    role: UserRole = UserRole.USER,
) -> UserData:
    return UserData(
        user_id=user_uuid,
        is_authorized=True,
        is_admin=is_admin,
        is_superadmin=is_superadmin,
        role=role,
        domain_name=domain,
    )


def _superadmin() -> UserData:
    return _user(is_admin=True, is_superadmin=True, role=UserRole.SUPERADMIN)


def _allow_entry(
    scope_type: AppConfigScopeType,
    *,
    config_name: str = "theme",
    write_access: AppConfigAccessLevel | None = None,
    read_access: AppConfigAccessLevel | None = None,
) -> AppConfigAllowListData:
    now = datetime.now(UTC)
    return AppConfigAllowListData(
        id=AppConfigAllowListID(uuid.uuid4()),
        config_name=config_name,
        scope_type=scope_type,
        rank=scope_type.default_rank(),
        read_access=read_access if read_access is not None else scope_type.default_read_access(),
        write_access=write_access
        if write_access is not None
        else scope_type.default_write_access(),
        created_at=now,
        updated_at=now,
    )


def _user_spec(scope_id: str = _USER_ID) -> AppConfigFragmentCreatorSpec:
    return AppConfigFragmentCreatorSpec(
        config_name="theme",
        scope_type=AppConfigScopeType.USER,
        scope_id=scope_id,
        config={"k": "v"},
    )


class TestAppConfigFragmentService:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigFragmentRepository)

    @pytest.fixture
    def mock_allow_list_repository(self) -> MagicMock:
        # Default: the ("theme", user) layer exists with the default policy (write=owner).
        repo = MagicMock(spec=AppConfigAllowListRepository)
        repo.by_config_and_scope = AsyncMock(return_value=_allow_entry(AppConfigScopeType.USER))
        return repo

    @pytest.fixture
    def service(
        self, mock_repository: MagicMock, mock_allow_list_repository: MagicMock
    ) -> AppConfigFragmentService:
        return AppConfigFragmentService(
            repository=mock_repository,
            allow_list_repository=mock_allow_list_repository,
        )

    # --- create (delegation, authorized owner) ---

    async def test_create_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragment = _fragment()
        mock_repository.create = AsyncMock(return_value=fragment)
        spec = _user_spec()

        result = await service.create(
            CreateAppConfigFragmentAction(creator_spec=spec, requester=_user())
        )

        assert result.fragment == fragment
        mock_repository.create.assert_called_once_with(Creator(spec=spec))

    # --- write authorization ---

    async def test_create_non_owner_rejected(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        mock_repository.create = AsyncMock()
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await service.create(
                CreateAppConfigFragmentAction(
                    creator_spec=_user_spec(), requester=_user(_OTHER_UUID)
                )
            )
        mock_repository.create.assert_not_called()

    async def test_create_superadmin_writes_public(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        mock_allow_list_repository.by_config_and_scope = AsyncMock(
            return_value=_allow_entry(AppConfigScopeType.PUBLIC)  # write=admin
        )
        fragment = _fragment(scope_type=AppConfigScopeType.PUBLIC, scope_id="public")
        mock_repository.create = AsyncMock(return_value=fragment)
        spec = AppConfigFragmentCreatorSpec(
            config_name="theme",
            scope_type=AppConfigScopeType.PUBLIC,
            scope_id="public",
            config={"k": "v"},
        )

        result = await service.create(
            CreateAppConfigFragmentAction(creator_spec=spec, requester=_superadmin())
        )

        assert result.fragment == fragment
        mock_repository.create.assert_called_once()

    async def test_create_non_admin_public_rejected(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        mock_allow_list_repository.by_config_and_scope = AsyncMock(
            return_value=_allow_entry(AppConfigScopeType.PUBLIC)  # write=admin
        )
        mock_repository.create = AsyncMock()
        spec = AppConfigFragmentCreatorSpec(
            config_name="theme",
            scope_type=AppConfigScopeType.PUBLIC,
            scope_id="public",
            config={"k": "v"},
        )
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await service.create(
                CreateAppConfigFragmentAction(creator_spec=spec, requester=_user())
            )
        mock_repository.create.assert_not_called()

    async def test_create_domain_non_admin_rejected(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        mock_allow_list_repository.by_config_and_scope = AsyncMock(
            return_value=_allow_entry(AppConfigScopeType.DOMAIN)  # write=admin
        )
        mock_repository.create = AsyncMock()
        spec = AppConfigFragmentCreatorSpec(
            config_name="theme",
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id="default",
            config={"k": "v"},
        )
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await service.create(
                CreateAppConfigFragmentAction(creator_spec=spec, requester=_user())
            )
        mock_repository.create.assert_not_called()

    async def test_create_missing_allow_list_rejected(
        self,
        service: AppConfigFragmentService,
        mock_repository: MagicMock,
        mock_allow_list_repository: MagicMock,
    ) -> None:
        mock_allow_list_repository.by_config_and_scope = AsyncMock(return_value=None)
        mock_repository.create = AsyncMock()
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await service.create(
                CreateAppConfigFragmentAction(creator_spec=_user_spec(), requester=_user())
            )
        mock_repository.create.assert_not_called()

    # --- get / search (no authz) ---

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
        assert [ref.element_id for ref in result.queried_refs] == [str(domain_id), _USER_ID]
        mock_repository.scoped_search.assert_called_once()
        called_querier, called_scopes = mock_repository.scoped_search.call_args.args
        assert called_querier is querier
        assert called_scopes[0].domain_id == domain_id
        assert called_scopes[1].user_id == _USER_UUID

    # --- update (loads fragment, then authorizes) ---

    async def test_update_owner_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        existing = _fragment()  # USER scope, scope_id == _USER_ID
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_repository.update = AsyncMock(return_value=existing)
        updater = Updater(
            spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
            pk_value=existing.id,
        )

        result = await service.update(
            UpdateAppConfigFragmentAction(updater=updater, requester=_user())
        )

        assert result.fragment == existing
        mock_repository.get_by_id.assert_called_once_with(existing.id)
        mock_repository.update.assert_called_once_with(updater)

    async def test_update_non_owner_rejected(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        existing = _fragment()  # owned by _USER_ID
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_repository.update = AsyncMock()
        updater = Updater(
            spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
            pk_value=existing.id,
        )

        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await service.update(
                UpdateAppConfigFragmentAction(updater=updater, requester=_user(_OTHER_UUID))
            )
        mock_repository.update.assert_not_called()

    # --- purge ---

    async def test_purge_owner_delegates_to_repository(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        existing = _fragment()
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_repository.purge = AsyncMock(return_value=existing)
        purger = Purger(row_class=AppConfigFragmentRow, pk_value=existing.id)

        result = await service.purge(PurgeAppConfigFragmentAction(purger=purger, requester=_user()))

        assert result.fragment == existing
        mock_repository.purge.assert_called_once_with(purger)

    async def test_purge_non_owner_rejected(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        existing = _fragment()
        mock_repository.get_by_id = AsyncMock(return_value=existing)
        mock_repository.purge = AsyncMock()
        purger = Purger(row_class=AppConfigFragmentRow, pk_value=existing.id)

        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await service.purge(
                PurgeAppConfigFragmentAction(purger=purger, requester=_user(_OTHER_UUID))
            )
        mock_repository.purge.assert_not_called()

    # --- bulk ---

    async def test_bulk_create_owner_delegates(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        fragments = [_fragment(), _fragment()]
        mock_repository.bulk_create = AsyncMock(
            return_value=AppConfigFragmentBulkResult(succeeded=fragments, failed=[])
        )
        specs = [_user_spec(), _user_spec()]

        result = await service.bulk_create(
            BulkCreateAppConfigFragmentAction(creator_specs=specs, requester=_user())
        )

        assert result.succeeded == fragments
        assert result.failed == []
        mock_repository.bulk_create.assert_called_once_with(BulkCreator(specs=specs))

    async def test_bulk_create_mixed_authz_partial(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        # item 0 owned by the caller (authorized), item 1 owned by another user (rejected).
        owned = _user_spec(_USER_ID)
        foreign = _user_spec(str(_OTHER_UUID))
        created = _fragment()
        mock_repository.bulk_create = AsyncMock(
            return_value=AppConfigFragmentBulkResult(succeeded=[created], failed=[])
        )

        result = await service.bulk_create(
            BulkCreateAppConfigFragmentAction(creator_specs=[owned, foreign], requester=_user())
        )

        mock_repository.bulk_create.assert_called_once_with(BulkCreator(specs=[owned]))
        assert result.succeeded == [created]
        assert [e.index for e in result.failed] == [1]

    async def test_bulk_create_remaps_repo_failure_indices(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        # item 0 unauthorized (foreign), item 1 authorized but fails at the repo.
        foreign = _user_spec(str(_OTHER_UUID))
        owned = _user_spec(_USER_ID)
        mock_repository.bulk_create = AsyncMock(
            return_value=AppConfigFragmentBulkResult(
                succeeded=[],
                failed=[AppConfigFragmentBulkItemError(index=0, message="db failure")],
            )
        )

        result = await service.bulk_create(
            BulkCreateAppConfigFragmentAction(creator_specs=[foreign, owned], requester=_user())
        )

        # the repo saw only [owned] (repo failure index 0); it must remap to batch index 1,
        # while the authz failure for [foreign] stays at index 0.
        mock_repository.bulk_create.assert_called_once_with(BulkCreator(specs=[owned]))
        assert sorted(e.index for e in result.failed) == [0, 1]

    async def test_bulk_update_authorizes_each_after_loading(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        owned = _fragment(scope_id=_USER_ID)
        foreign = _fragment(scope_id=str(_OTHER_UUID))
        mock_repository.get_by_id = AsyncMock(side_effect=[owned, foreign])
        mock_repository.bulk_update = AsyncMock(
            return_value=AppConfigFragmentBulkResult(succeeded=[owned], failed=[])
        )
        updaters = [
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
                pk_value=owned.id,
            ),
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 3})),
                pk_value=foreign.id,
            ),
        ]

        result = await service.bulk_update(
            BulkUpdateAppConfigFragmentAction(updaters=updaters, requester=_user())
        )

        called_updaters = mock_repository.bulk_update.call_args.args[0]
        assert [u.pk_value for u in called_updaters] == [owned.id]
        assert result.succeeded == [owned]
        assert [e.index for e in result.failed] == [1]

    async def test_bulk_purge_missing_fragment_is_per_item_failure(
        self, service: AppConfigFragmentService, mock_repository: MagicMock
    ) -> None:
        owned = _fragment(scope_id=_USER_ID)
        missing_id = AppConfigFragmentID(uuid.uuid4())
        mock_repository.get_by_id = AsyncMock(
            side_effect=[owned, AppConfigFragmentNotFound(f"{missing_id} not found")]
        )
        mock_repository.bulk_purge = AsyncMock(
            return_value=AppConfigFragmentBulkResult(succeeded=[owned], failed=[])
        )
        purgers = [
            Purger(row_class=AppConfigFragmentRow, pk_value=owned.id),
            Purger(row_class=AppConfigFragmentRow, pk_value=missing_id),
        ]

        result = await service.bulk_purge(
            BulkPurgeAppConfigFragmentAction(purgers=purgers, requester=_user())
        )

        called_purgers = mock_repository.bulk_purge.call_args.args[0]
        assert [p.pk_value for p in called_purgers] == [owned.id]
        assert result.succeeded == [owned]
        assert [e.index for e in result.failed] == [1]


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


class TestAccessLevelPredicate:
    """AppConfigAccessLevel.is_satisfied_by tier resolution."""

    def test_anonymous_only_satisfies_public(self) -> None:
        assert AppConfigAccessLevel.PUBLIC.is_satisfied_by(None, AppConfigScopeType.USER, _USER_ID)
        assert not AppConfigAccessLevel.OWNER.is_satisfied_by(
            None, AppConfigScopeType.USER, _USER_ID
        )
        assert not AppConfigAccessLevel.ADMIN.is_satisfied_by(
            None, AppConfigScopeType.PUBLIC, "public"
        )

    def test_superadmin_satisfies_every_tier(self) -> None:
        for level in AppConfigAccessLevel:
            assert level.is_satisfied_by(_superadmin(), AppConfigScopeType.PUBLIC, "public")

    def test_owner_user_scope(self) -> None:
        assert AppConfigAccessLevel.OWNER.is_satisfied_by(
            _user(), AppConfigScopeType.USER, _USER_ID
        )
        assert not AppConfigAccessLevel.OWNER.is_satisfied_by(
            _user(_OTHER_UUID), AppConfigScopeType.USER, _USER_ID
        )

    def test_owner_domain_scope_requires_domain_admin(self) -> None:
        domain_admin = _user(is_admin=True, domain="default", role=UserRole.ADMIN)
        assert AppConfigAccessLevel.OWNER.is_satisfied_by(
            domain_admin, AppConfigScopeType.DOMAIN, "default"
        )
        assert not AppConfigAccessLevel.OWNER.is_satisfied_by(
            domain_admin, AppConfigScopeType.DOMAIN, "other-domain"
        )
        assert not AppConfigAccessLevel.OWNER.is_satisfied_by(
            _user(), AppConfigScopeType.DOMAIN, "default"
        )

    def test_admin_tier_needs_superadmin(self) -> None:
        assert not AppConfigAccessLevel.ADMIN.is_satisfied_by(
            _user(is_admin=True, role=UserRole.ADMIN), AppConfigScopeType.PUBLIC, "public"
        )
        assert AppConfigAccessLevel.ADMIN.is_satisfied_by(
            _superadmin(), AppConfigScopeType.PUBLIC, "public"
        )
