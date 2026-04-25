"""Repository tests for AppConfigPolicy with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.errors.app_config import AppConfigPolicyNotFound
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_policy.admin_repository import (
    AppConfigPolicyAdminRepository,
)
from ai.backend.manager.repositories.app_config_policy.repository import (
    AppConfigPolicyRepository,
)
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
        return AppConfigPolicyRepository(db)

    @pytest.fixture
    def admin_repository(self, db: ExtendedAsyncSAEngine) -> AppConfigPolicyAdminRepository:
        return AppConfigPolicyAdminRepository(db)

    async def test_create_and_get_by_config_name(
        self,
        repository: AppConfigPolicyRepository,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        created = await admin_repository.create(
            config_name="theme",
            scope_sources=["domain"],
        )
        assert created.config_name == "theme"
        assert list(created.scope_sources) == ["domain"]

        fetched = await repository.get("theme")
        assert fetched is not None
        assert fetched.id == created.id
        assert list(fetched.scope_sources) == ["domain"]

    async def test_get_by_id(
        self,
        repository: AppConfigPolicyRepository,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        created = await admin_repository.create(
            config_name="preferences",
            scope_sources=["domain_user_defaults", "user"],
        )

        fetched = await repository.get_by_id(created.id)
        assert fetched is not None
        assert fetched.config_name == "preferences"
        assert list(fetched.scope_sources) == ["domain_user_defaults", "user"]

    async def test_get_returns_none_for_missing_config_name(
        self,
        repository: AppConfigPolicyRepository,
    ) -> None:
        assert await repository.get("nonexistent") is None


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
        return AppConfigPolicyAdminRepository(db)

    async def test_update_replaces_scope_sources(
        self,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        await admin_repository.create(
            config_name="theme",
            scope_sources=["domain"],
        )
        updated = await admin_repository.update(
            config_name="theme",
            scope_sources=["domain", "user"],
        )
        assert updated is not None
        assert list(updated.scope_sources) == ["domain", "user"]

    async def test_update_raises_for_missing_config_name(
        self,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        with pytest.raises(AppConfigPolicyNotFound):
            await admin_repository.update(
                config_name="nonexistent",
                scope_sources=["user"],
            )

    async def test_purge_existing_policy_returns_true(
        self,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        await admin_repository.create(
            config_name="theme",
            scope_sources=["domain"],
        )
        assert await admin_repository.purge("theme") is True

    async def test_purge_missing_policy_returns_false(
        self,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        assert await admin_repository.purge("nonexistent") is False
