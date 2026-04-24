"""Repository tests for AppConfigFragment with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentKey,
    AppConfigScopeType,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.admin_repository import (
    AppConfigFragmentAdminRepository,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_policy.admin_repository import (
    AppConfigPolicyAdminRepository,
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
                AppConfigPolicyRow,  # Parent (FK target)
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

    @pytest.fixture
    async def policy_for_theme(self, db: ExtendedAsyncSAEngine) -> AsyncGenerator[None, None]:
        # Required-policy invariant: a policy must exist before any
        # fragment can reference its `name`.
        await AppConfigPolicyAdminRepository(db).create(
            config_name="theme",
            scope_sources=["domain"],
        )
        yield

    async def test_create_and_get_by_key(
        self,
        policy_for_theme: None,
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
            extra_config={"color": "blue"},
        )
        assert created.scope_type == AppConfigScopeType.DOMAIN
        assert created.scope_id == "default"
        assert created.name == "theme"
        assert dict(created.extra_config) == {"color": "blue"}

        fetched = await repository.get(key)
        assert fetched is not None
        assert fetched.id == created.id
        assert dict(fetched.extra_config) == {"color": "blue"}

    async def test_get_by_id(
        self,
        policy_for_theme: None,
        repository: AppConfigFragmentRepository,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        created = await admin_repository.create(
            key=AppConfigFragmentKey(
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                name="theme",
            ),
            extra_config={"density": "comfortable"},
        )

        fetched = await repository.get_by_id(created.id)
        assert fetched is not None
        assert fetched.scope_type == AppConfigScopeType.PUBLIC
        assert dict(fetched.extra_config) == {"density": "comfortable"}

    async def test_get_returns_none_for_missing_key(
        self,
        repository: AppConfigFragmentRepository,
    ) -> None:
        assert (
            await repository.get(
                AppConfigFragmentKey(
                    scope_type=AppConfigScopeType.DOMAIN,
                    scope_id="missing",
                    name="theme",
                )
            )
            is None
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
                AppConfigPolicyRow,
                AppConfigFragmentRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def admin_repository(self, db: ExtendedAsyncSAEngine) -> AppConfigFragmentAdminRepository:
        return AppConfigFragmentAdminRepository(db)

    @pytest.fixture
    async def policy_for_theme(self, db: ExtendedAsyncSAEngine) -> AsyncGenerator[None, None]:
        await AppConfigPolicyAdminRepository(db).create(
            config_name="theme",
            scope_sources=["domain"],
        )
        yield

    async def test_update_replaces_extra_config(
        self,
        policy_for_theme: None,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        key = AppConfigFragmentKey(
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id="default",
            name="theme",
        )
        await admin_repository.create(key=key, extra_config={"color": "blue"})
        updated = await admin_repository.update(
            key=key, extra_config={"color": "red", "density": "compact"}
        )
        assert updated is not None
        assert dict(updated.extra_config) == {"color": "red", "density": "compact"}

    async def test_update_returns_none_for_missing_key(
        self,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        assert (
            await admin_repository.update(
                key=AppConfigFragmentKey(
                    scope_type=AppConfigScopeType.DOMAIN,
                    scope_id="missing",
                    name="theme",
                ),
                extra_config={"color": "blue"},
            )
            is None
        )

    async def test_purge_existing_fragment_returns_true(
        self,
        policy_for_theme: None,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        key = AppConfigFragmentKey(
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id="default",
            name="theme",
        )
        await admin_repository.create(key=key, extra_config={})
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

    async def test_create_without_matching_policy_violates_fk(
        self,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        # Required-policy invariant (BEP-1052 §1) — DB-level FK is the
        # backstop when the service layer's check is bypassed.
        with pytest.raises(sa.exc.IntegrityError):
            await admin_repository.create(
                key=AppConfigFragmentKey(
                    scope_type=AppConfigScopeType.DOMAIN,
                    scope_id="default",
                    name="no-such-policy",
                ),
                extra_config={"color": "blue"},
            )
