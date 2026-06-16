"""Repository tests for AppConfigFragment with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentKey,
    AppConfigScopeType,
)
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.admin_repository import (
    AppConfigFragmentAdminRepository,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.testutils.db import with_tables


class TestAppConfigFragmentRepository:
    """Read-side tests for AppConfigFragmentRepository."""

    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                AppConfigFragmentRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db: ExtendedAsyncSAEngine) -> AppConfigFragmentRepository:
        return AppConfigFragmentRepository(db)

    @pytest.fixture
    def admin_repository(self, db: ExtendedAsyncSAEngine) -> AppConfigFragmentAdminRepository:
        return AppConfigFragmentAdminRepository(db)

    async def test_create_and_get_by_key(
        self,
        repository: AppConfigFragmentRepository,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        key = AppConfigFragmentKey(
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id="default",
            name="theme",
        )
        created = await admin_repository.create(
            key=key,
            config={"color": "blue"},
        )
        assert created.scope_type == AppConfigScopeType.DOMAIN
        assert created.scope_id == "default"
        assert created.name == "theme"
        # First fragment for `theme` gets the base next-value rank.
        assert created.rank == 100
        assert created.config is not None
        assert dict(created.config) == {"color": "blue"}

        fetched = await repository.get_by_key(key)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.config is not None
        assert dict(fetched.config) == {"color": "blue"}

    async def test_get_by_id(
        self,
        repository: AppConfigFragmentRepository,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        created = await admin_repository.create(
            key=AppConfigFragmentKey(
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                name="theme",
            ),
            config={"density": "comfortable"},
        )
        # First fragment for `theme` gets the base next-value rank.
        assert created.rank == 100

        fetched = await repository.get_by_id(created.id)
        assert fetched is not None
        assert fetched.scope_type == AppConfigScopeType.PUBLIC
        assert fetched.config is not None
        assert dict(fetched.config) == {"density": "comfortable"}

    async def test_get_raises_for_missing_key(
        self,
        repository: AppConfigFragmentRepository,
    ) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_key(
                AppConfigFragmentKey(
                    scope_type=AppConfigScopeType.DOMAIN,
                    scope_id="missing",
                    name="theme",
                )
            )


class TestAppConfigFragmentAdminRepository:
    """Mutation-side tests for AppConfigFragmentAdminRepository."""

    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                AppConfigFragmentRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def admin_repository(self, db: ExtendedAsyncSAEngine) -> AppConfigFragmentAdminRepository:
        return AppConfigFragmentAdminRepository(db)

    async def test_update_replaces_config(
        self,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        key = AppConfigFragmentKey(
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id="default",
            name="theme",
        )
        await admin_repository.create(key=key, config={"color": "blue"})
        updated = await admin_repository.update(
            key=key, config={"color": "red", "density": "compact"}
        )
        assert updated is not None
        assert updated.config is not None
        assert dict(updated.config) == {"color": "red", "density": "compact"}

    async def test_update_raises_for_missing_key(
        self,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await admin_repository.update(
                key=AppConfigFragmentKey(
                    scope_type=AppConfigScopeType.DOMAIN,
                    scope_id="missing",
                    name="theme",
                ),
                config={"color": "blue"},
            )

    async def test_purge_existing_fragment_returns_true(
        self,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        key = AppConfigFragmentKey(
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id="default",
            name="theme",
        )
        await admin_repository.create(key=key, config={})
        assert await admin_repository.purge(key) is True

    async def test_purge_missing_fragment_returns_false(
        self,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        assert (
            await admin_repository.purge(
                AppConfigFragmentKey(
                    scope_type=AppConfigScopeType.DOMAIN,
                    scope_id="missing",
                    name="theme",
                )
            )
            is False
        )

    async def test_rank_assigned_by_next_value(
        self,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        # Fragments sharing a `name` get a monotonic next-value rank
        # (MAX + gap within the name), like DeploymentRevisionPreset —
        # not a per-scope_type tier.
        first = await admin_repository.create(
            key=AppConfigFragmentKey(
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                name="theme",
            ),
            config={"density": "comfortable"},
        )
        second = await admin_repository.create(
            key=AppConfigFragmentKey(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id="default",
                name="theme",
            ),
            config={"color": "blue"},
        )
        assert first.rank == 100
        assert second.rank == 200
