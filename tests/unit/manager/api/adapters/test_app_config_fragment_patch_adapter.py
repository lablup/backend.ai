"""Unit tests for the app config fragment adapter's key patch: which action carries the
patch upserters, and the owner they name."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserData
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentEntry,
    AppConfigFragmentPatch,
    AppConfigScopeRef,
    MyPatchAppConfigFragmentsInput,
    ScopedPatchAppConfigFragmentsInput,
)
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.models.app_config_fragment.upserters import (
    AppConfigFragmentPatchUpserter,
    PublicAppConfigFragmentPatchUpserter,
)
from ai.backend.manager.models.user.row import UserRole

_PATCH = AppConfigFragmentPatch(
    config_name="theme",
    set=[AppConfigFragmentEntry(key="themeFamily", value={"a": 1})],
    unset=["banner"],
)


@pytest.fixture
def processors() -> MagicMock:
    result = MagicMock()
    result.fragment_bulk_upsert.run = AsyncMock(return_value=MagicMock(items=[]))
    result.fragment_global_bulk_upsert.run = AsyncMock(return_value=MagicMock(items=[]))
    return result


@pytest.fixture
def adapter(processors: MagicMock) -> AppConfigFragmentAdapter:
    return AppConfigFragmentAdapter(processors)


def _action(processors: MagicMock, name: str) -> Any:
    return getattr(processors, name).run.call_args[0][0]


class TestMyAtomicBulkPatch:
    async def test_patches_at_the_current_users_own_scope(
        self, adapter: AppConfigFragmentAdapter, processors: MagicMock
    ) -> None:
        user = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
            domain_id=DomainID(uuid.uuid4()),
        )

        with with_user_context(user):
            await adapter.my_atomic_bulk_patch(MyPatchAppConfigFragmentsInput(items=[_PATCH]))

        action = _action(processors, "fragment_bulk_upsert")
        assert action.owner == UserID(user.user_id)
        [upserter] = action.upserters
        assert isinstance(upserter, AppConfigFragmentPatchUpserter)
        assert upserter.owner == UserID(user.user_id)
        assert upserter.config_name == "theme"
        assert upserter.config == {"themeFamily": {"a": 1}}
        assert list(upserter.unset) == ["banner"]


class TestScopedAtomicBulkPatch:
    async def test_a_domain_scope_patches_under_that_owner(
        self, adapter: AppConfigFragmentAdapter, processors: MagicMock
    ) -> None:
        domain_id = uuid.uuid4()

        await adapter.scoped_atomic_bulk_patch(
            ScopedPatchAppConfigFragmentsInput(
                scope=AppConfigScopeRef(
                    scope_type=AppConfigScopeType.DOMAIN, scope_id=AppConfigScopeID(domain_id)
                ),
                items=[_PATCH],
            )
        )

        action = _action(processors, "fragment_bulk_upsert")
        assert action.owner == DomainID(domain_id)
        assert all(
            isinstance(upserter, AppConfigFragmentPatchUpserter) for upserter in action.upserters
        )
        processors.fragment_global_bulk_upsert.run.assert_not_called()

    async def test_the_public_scope_runs_behind_the_global_gate(
        self, adapter: AppConfigFragmentAdapter, processors: MagicMock
    ) -> None:
        await adapter.scoped_atomic_bulk_patch(
            ScopedPatchAppConfigFragmentsInput(
                scope=AppConfigScopeRef(scope_type=AppConfigScopeType.PUBLIC),
                items=[_PATCH],
            )
        )

        action = _action(processors, "fragment_global_bulk_upsert")
        [upserter] = action.upserters
        assert isinstance(upserter, PublicAppConfigFragmentPatchUpserter)
        assert upserter.config == {"themeFamily": {"a": 1}}
        processors.fragment_bulk_upsert.run.assert_not_called()
