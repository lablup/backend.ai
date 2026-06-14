"""Repository tests for AppConfigPolicy with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.manager.errors.app_config import AppConfigPolicyNotFound
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_policy.admin_repository import (
    AppConfigPolicyAdminRepository,
)
from ai.backend.manager.repositories.app_config_policy.repository import (
    AppConfigPolicyRepository,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.testutils.db import with_tables


class TestAppConfigPolicyRepository:
    """Read-side tests for AppConfigPolicyRepository."""

    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [AppConfigPolicyRow],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db: ExtendedAsyncSAEngine) -> AppConfigPolicyRepository:
        return AppConfigPolicyRepository(DBOpsProvider(db))

    @pytest.fixture
    def admin_repository(self, db: ExtendedAsyncSAEngine) -> AppConfigPolicyAdminRepository:
        return AppConfigPolicyAdminRepository(DBOpsProvider(db))

    async def test_create_and_get_by_id(
        self,
        repository: AppConfigPolicyRepository,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        created = await admin_repository.create(
            config_name="theme",
            scope_sources=[AppConfigScopeType.DOMAIN],
        )
        assert created.config_name == "theme"
        assert list(created.scope_sources) == [AppConfigScopeType.DOMAIN]

        fetched = await repository.get_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert list(fetched.scope_sources) == [AppConfigScopeType.DOMAIN]

    async def test_get_by_id_returns_full_record(
        self,
        repository: AppConfigPolicyRepository,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        created = await admin_repository.create(
            config_name="preferences",
            scope_sources=[AppConfigScopeType.DOMAIN_USER_DEFAULTS, AppConfigScopeType.USER],
        )

        fetched = await repository.get_by_id(created.id)
        assert fetched is not None
        assert fetched.config_name == "preferences"
        assert list(fetched.scope_sources) == [AppConfigScopeType.DOMAIN_USER_DEFAULTS, AppConfigScopeType.USER]

    async def test_get_by_id_raises_for_missing(
        self,
        repository: AppConfigPolicyRepository,
    ) -> None:
        with pytest.raises(AppConfigPolicyNotFound):
            await repository.get_by_id(AppConfigPolicyID(uuid.uuid4()))


class TestAppConfigPolicyAdminRepository:
    """Mutation-side tests for AppConfigPolicyAdminRepository."""

    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [AppConfigPolicyRow],
        ):
            yield database_connection

    @pytest.fixture
    def admin_repository(self, db: ExtendedAsyncSAEngine) -> AppConfigPolicyAdminRepository:
        return AppConfigPolicyAdminRepository(DBOpsProvider(db))

    async def test_update_replaces_scope_sources(
        self,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        created = await admin_repository.create(
            config_name="theme",
            scope_sources=[AppConfigScopeType.DOMAIN],
        )
        updated = await admin_repository.update(
            id=created.id,
            scope_sources=[AppConfigScopeType.DOMAIN, AppConfigScopeType.USER],
        )
        assert updated is not None
        assert list(updated.scope_sources) == [AppConfigScopeType.DOMAIN, AppConfigScopeType.USER]

    async def test_update_raises_for_missing_id(
        self,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        with pytest.raises(AppConfigPolicyNotFound):
            await admin_repository.update(
                id=AppConfigPolicyID(uuid.uuid4()),
                scope_sources=[AppConfigScopeType.USER],
            )

    async def test_purge_existing_policy_returns_true(
        self,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        created = await admin_repository.create(
            config_name="theme",
            scope_sources=[AppConfigScopeType.DOMAIN],
        )
        assert await admin_repository.purge(created.id) is True

    async def test_purge_missing_policy_returns_false(
        self,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        assert await admin_repository.purge(AppConfigPolicyID(uuid.uuid4())) is False
