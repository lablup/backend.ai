"""Component tests for ``need_password_change`` on the strawberry user update mutations."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.api.gql.schema import schema as strawberry_schema
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.user.row import users
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.user.processors import UserProcessors

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData

_OLD_PASSWORD_CHANGED_AT = datetime(2000, 1, 1, tzinfo=UTC)

_UPDATE_USER_V2 = """
mutation UpdateUserV2($input: UpdateUserV2Input!) {
    updateUserV2(input: $input) {
        user { id }
    }
}
"""

_ADMIN_UPDATE_USER_V2 = """
mutation AdminUpdateUserV2($userId: UUID!, $input: UpdateUserV2Input!) {
    adminUpdateUserV2(userId: $userId, input: $input) {
        user { id }
    }
}
"""


async def _call_gql(
    registry: BackendAIClientRegistry,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    result = await registry._client._request(
        "POST",
        "/admin/gql/strawberry",
        json={"query": query, "variables": variables},
    )
    assert result is not None
    return cast(dict[str, Any], result)


async def _call_gql_ok(
    registry: BackendAIClientRegistry,
    query: str,
    variables: dict[str, Any],
) -> None:
    response = await _call_gql(registry, query, variables)
    assert not response.get("errors"), f"Unexpected GQL errors: {response.get('errors')}"


async def _require_password_change(db_engine: SAEngine, user: UserFixtureData) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(users)
            .where(users.c.uuid == str(user.user_uuid))
            .values(need_password_change=True, password_changed_at=_OLD_PASSWORD_CHANGED_AT)
        )


async def _password_state(db_engine: SAEngine, user: UserFixtureData) -> sa.Row[Any]:
    async with db_engine.begin() as conn:
        result = await conn.execute(
            sa.select(users.c.need_password_change, users.c.password_changed_at).where(
                users.c.uuid == str(user.user_uuid)
            )
        )
        return result.one()


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    user_processors: UserProcessors,
    domain_processors: DomainProcessors,
    config_provider: ManagerConfigProvider,
) -> list[RouteRegistry]:
    """Register the strawberry GQL endpoint with a real user adapter."""
    mock_gql_deps = MagicMock()
    mock_gql_deps.processors.user = user_processors
    mock_gql_deps.config_provider = config_provider
    mock_gql_deps.adapters.user = UserAdapter(
        user_processors,
        domain_processors,
        auth_config=config_provider.config.auth,
        key_provider_pool=KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(),
                gql_deps=mock_gql_deps,
                strawberry_schema=strawberry_schema,
                public_strawberry_schema=MagicMock(),
            ),
            route_deps,
            sub_registries=[],
            gql_ws_handler=MagicMock(),
        ),
    ]


@pytest.fixture()
async def user_needing_password_change(
    db_engine: SAEngine,
    regular_user_fixture: UserFixtureData,
) -> UserFixtureData:
    await _require_password_change(db_engine, regular_user_fixture)
    return regular_user_fixture


@pytest.fixture()
async def admin_needing_password_change(
    db_engine: SAEngine,
    admin_user_fixture: UserFixtureData,
) -> UserFixtureData:
    await _require_password_change(db_engine, admin_user_fixture)
    return admin_user_fixture


class TestUpdateUserV2NeedPasswordChange:
    async def test_own_password_change_clears_flag(
        self,
        user_registry: BackendAIClientRegistry,
        user_needing_password_change: UserFixtureData,
        db_engine: SAEngine,
    ) -> None:
        await _call_gql_ok(
            user_registry,
            _UPDATE_USER_V2,
            {"input": {"password": secrets.token_urlsafe(12)}},
        )

        state = await _password_state(db_engine, user_needing_password_change)
        assert state.need_password_change is False
        assert state.password_changed_at > _OLD_PASSWORD_CHANGED_AT

    async def test_own_update_without_password_keeps_flag(
        self,
        user_registry: BackendAIClientRegistry,
        user_needing_password_change: UserFixtureData,
        db_engine: SAEngine,
    ) -> None:
        await _call_gql_ok(
            user_registry,
            _UPDATE_USER_V2,
            {"input": {"fullName": "Renamed User"}},
        )

        state = await _password_state(db_engine, user_needing_password_change)
        assert state.need_password_change is True
        assert state.password_changed_at == _OLD_PASSWORD_CHANGED_AT

    async def test_admin_password_change_keeps_flag(
        self,
        admin_registry: BackendAIClientRegistry,
        user_needing_password_change: UserFixtureData,
        db_engine: SAEngine,
    ) -> None:
        await _call_gql_ok(
            admin_registry,
            _ADMIN_UPDATE_USER_V2,
            {
                "userId": str(user_needing_password_change.user_uuid),
                "input": {"password": secrets.token_urlsafe(12)},
            },
        )

        state = await _password_state(db_engine, user_needing_password_change)
        assert state.need_password_change is True
        assert state.password_changed_at > _OLD_PASSWORD_CHANGED_AT

    async def test_own_password_change_requiring_change_is_rejected(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_needing_password_change: UserFixtureData,
        db_engine: SAEngine,
    ) -> None:
        response = await _call_gql(
            admin_registry,
            _UPDATE_USER_V2,
            {"input": {"password": secrets.token_urlsafe(12), "needPasswordChange": True}},
        )

        codes = [e.get("extensions", {}).get("code") for e in response.get("errors") or []]
        assert codes == ["user_update_bad-request"]
        state = await _password_state(db_engine, admin_needing_password_change)
        assert state.need_password_change is True
        assert state.password_changed_at == _OLD_PASSWORD_CHANGED_AT
