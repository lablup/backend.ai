"""Component tests for keypair self-service operations via the strawberry GQL endpoint."""

from __future__ import annotations

import secrets
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.manager.api.adapters.user import UserAdapter
from ai.backend.manager.api.gql.schema import schema as strawberry_schema
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.user.handler import UserHandler
from ai.backend.manager.api.rest.user.registry import register_user_routes
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.services.user.processors import UserProcessors

# ---------------------------------------------------------------------------
# GQL query strings
# ---------------------------------------------------------------------------

_UPDATE_MY_KEYPAIR = """
mutation UpdateMyKeypair($accessKey: String!, $isActive: Boolean!) {
    updateMyKeypair(input: {accessKey: $accessKey, isActive: $isActive}) {
        success
    }
}
"""

_SWITCH_MY_MAIN_ACCESS_KEY = """
mutation SwitchMyMainAccessKey($accessKey: String!) {
    switchMyMainAccessKey(input: {accessKey: $accessKey}) {
        success
    }
}
"""

_ISSUE_MY_KEYPAIR = """
mutation IssueMyKeypair {
    issueMyKeypair {
        accessKey
        secretKey
    }
}
"""

# GQL error extension codes produced by GQLExceptionHandlerExtension
# ErrorCode.__str__() formats as "{domain}_{operation}_{error_detail}" (underscore-separated)
_GQL_ERR_FORBIDDEN = "keypair_read_forbidden"
_GQL_ERR_NOT_FOUND = "keypair_read_not-found"


# ---------------------------------------------------------------------------
# GQL HTTP helper
# ---------------------------------------------------------------------------


async def _call_gql(
    registry: BackendAIClientRegistry,
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """POST to /admin/gql/strawberry and return the raw JSON response dict."""
    result = await registry._client._request(
        "POST",
        "/admin/gql/strawberry",
        json={"query": query, "variables": variables or {}},
    )
    assert result is not None, "Expected a non-null JSON response from the GQL endpoint"
    return cast(dict[str, Any], result)


def _assert_gql_success(response: dict[str, Any], field: str) -> dict[str, Any]:
    """Assert no GQL errors and return the named data field."""
    assert not response.get("errors"), f"Unexpected GQL errors: {response.get('errors')}"
    data = response.get("data", {})
    assert data is not None
    return cast(dict[str, Any], data[field])


def _gql_error_codes(response: dict[str, Any]) -> list[str]:
    """Extract extension error codes from GQL error entries."""
    return [e.get("extensions", {}).get("code", "") for e in (response.get("errors") or [])]


# ---------------------------------------------------------------------------
# server_module_registries override
#
# This fixture overrides the user-conftest version so that the admin
# sub-app serves the REAL strawberry schema instead of a MagicMock.
# Only the UserProcessors (user domain) is real; the rest of the
# Processors and GQLContextDeps fields are mocked because the
# update_my_keypair / switch_my_main_access_key mutations only need
# processors.user.
# ---------------------------------------------------------------------------


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    user_processors: UserProcessors,
    config_provider: ManagerConfigProvider,
) -> list[RouteRegistry]:
    """Register user REST routes + real strawberry GQL for keypair-ops tests."""
    # Minimal Processors mock: only .user is needed by the keypair mutations.
    mock_processors = MagicMock()
    mock_processors.user = user_processors

    # Minimal GQLContextDeps mock: real config_provider so GQLValidationExtension
    # can read api.allow_graphql_schema_introspection and api.max_gql_query_depth.
    mock_gql_deps = MagicMock()
    mock_gql_deps.processors = mock_processors
    mock_gql_deps.config_provider = config_provider
    mock_gql_deps.adapters.user = UserAdapter(processors=mock_processors, auth_config=None)  # type: ignore[arg-type]

    user_registry = register_user_routes(
        UserHandler(user=user_processors, config_provider=config_provider),
        route_deps,
    )
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(),
                gql_deps=mock_gql_deps,
                strawberry_schema=strawberry_schema,
            ),
            route_deps,
            sub_registries=[user_registry],
        ),
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUpdateMyKeypair:
    """Component tests for the updateMyKeypair GQL mutation.

    Each test exercises a distinct success / failure scenario defined in
    the BA-5294 success criteria.
    """

    async def test_deactivate_own_keypair(
        self,
        user_registry: BackendAIClientRegistry,
        regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """S-1: updateMyKeypair(isActive=false) → keypairs.is_active=False in DB."""
        access_key: str = regular_user_fixture.keypair.access_key

        response = await _call_gql(
            user_registry,
            _UPDATE_MY_KEYPAIR,
            {"accessKey": access_key, "isActive": False},
        )
        payload = _assert_gql_success(response, "updateMyKeypair")
        assert payload["success"] is True

        async with db_engine.begin() as conn:
            row = await conn.execute(
                sa.select(keypairs.c.is_active).where(keypairs.c.access_key == access_key)
            )
            is_active = row.scalar()
        assert is_active is False, "Keypair should be deactivated in DB"

    async def test_activate_own_keypair(
        self,
        user_registry: BackendAIClientRegistry,
        db_engine: SAEngine,
    ) -> None:
        """S-2: updateMyKeypair(isActive=false) then (isActive=true) → is_active=True in DB.

        Uses a secondary keypair so that the primary keypair (used for auth) stays active.
        """
        # Issue a secondary keypair — the primary keypair used by user_registry remains active.
        issue_resp = await _call_gql(user_registry, _ISSUE_MY_KEYPAIR)
        issue_payload = _assert_gql_success(issue_resp, "issueMyKeypair")
        secondary_ak: str = issue_payload["accessKey"]

        try:
            # Deactivate the secondary keypair (primary keypair still active → auth works).
            deact = await _call_gql(
                user_registry,
                _UPDATE_MY_KEYPAIR,
                {"accessKey": secondary_ak, "isActive": False},
            )
            _assert_gql_success(deact, "updateMyKeypair")

            # Reactivate the secondary keypair — still authenticated via primary.
            response = await _call_gql(
                user_registry,
                _UPDATE_MY_KEYPAIR,
                {"accessKey": secondary_ak, "isActive": True},
            )
            payload = _assert_gql_success(response, "updateMyKeypair")
            assert payload["success"] is True

            async with db_engine.begin() as conn:
                row = await conn.execute(
                    sa.select(keypairs.c.is_active).where(keypairs.c.access_key == secondary_ak)
                )
                is_active = row.scalar()
            assert is_active is True, "Secondary keypair should be reactivated in DB"
        finally:
            # Clean up: remove the extra keypair to keep DB consistent.
            async with db_engine.begin() as conn:
                await conn.execute(keypairs.delete().where(keypairs.c.access_key == secondary_ak))

    async def test_update_another_users_keypair_raises_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
        admin_user_fixture: Any,
    ) -> None:
        """S-3: updateMyKeypair with another user's accessKey → KeyPairForbidden."""
        other_access_key: str = admin_user_fixture.keypair.access_key

        response = await _call_gql(
            user_registry,
            _UPDATE_MY_KEYPAIR,
            {"accessKey": other_access_key, "isActive": False},
        )
        assert response.get("errors"), "Expected a GQL error for cross-user keypair update"
        codes = _gql_error_codes(response)
        assert any(_GQL_ERR_FORBIDDEN in code for code in codes), (
            f"Expected forbidden error code, got: {codes}"
        )

    async def test_update_nonexistent_access_key_raises_not_found(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """S-4: updateMyKeypair with a non-existent accessKey → KeyPairNotFound."""
        fake_ak = f"AKFAKE{secrets.token_hex(7).upper()}"

        response = await _call_gql(
            user_registry,
            _UPDATE_MY_KEYPAIR,
            {"accessKey": fake_ak, "isActive": False},
        )
        assert response.get("errors"), "Expected a GQL error for non-existent access key"
        codes = _gql_error_codes(response)
        assert any(_GQL_ERR_NOT_FOUND in code for code in codes), (
            f"Expected not-found error code, got: {codes}"
        )

    async def test_switch_main_to_inactive_keypair_raises_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
        db_engine: SAEngine,
    ) -> None:
        """S-5: Deactivate a keypair, then switchMyMainAccessKey → KeyPairForbidden."""
        # Issue a second keypair so we can deactivate it without locking out the user.
        issue_resp = await _call_gql(user_registry, _ISSUE_MY_KEYPAIR)
        issue_payload = _assert_gql_success(issue_resp, "issueMyKeypair")
        new_access_key: str = issue_payload["accessKey"]

        try:
            # Deactivate the newly-issued keypair.
            deact = await _call_gql(
                user_registry,
                _UPDATE_MY_KEYPAIR,
                {"accessKey": new_access_key, "isActive": False},
            )
            _assert_gql_success(deact, "updateMyKeypair")

            # Attempt to set the now-inactive keypair as the main one.
            switch_resp = await _call_gql(
                user_registry,
                _SWITCH_MY_MAIN_ACCESS_KEY,
                {"accessKey": new_access_key},
            )
            assert switch_resp.get("errors"), (
                "Expected a GQL error when switching to an inactive keypair"
            )
            codes = _gql_error_codes(switch_resp)
            assert any(_GQL_ERR_FORBIDDEN in code for code in codes), (
                f"Expected forbidden error code, got: {codes}"
            )
        finally:
            # Clean up the extra keypair to keep DB consistent.
            async with db_engine.begin() as conn:
                await conn.execute(keypairs.delete().where(keypairs.c.access_key == new_access_key))
