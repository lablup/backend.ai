"""Component test for per-request enforcement of the shared DataLoader cache.

The shared loader keeps ``cache=True`` with a process-global cache that is never
cleared, so a value loaded by one request is served from cache to any later request
that loads the same key, without re-invoking ``load_fn``. This test asserts the
*desired* behavior: an authorization check performed inside ``load_fn`` must be
enforced for every request.

It is expected to FAIL against the current implementation: a cache hit skips
``load_fn`` (and its check) entirely, so a different user receives another user's
previously authorized result. Requests run sequentially, so no probe barrier is used.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders

_AUTHZ_QUERY = "query($id: ID!) { authzProbe(id: $id) }"


@pytest.fixture()
def data_loaders() -> DataLoaders:
    """Shared DataLoaders without a probe barrier (these requests run sequentially)."""
    return DataLoaders(MagicMock())


async def _authz_probe(registry: BackendAIClientRegistry, id_: str) -> dict[str, Any]:
    """Call authzProbe and return the raw response (so errors are observable)."""
    result = cast(
        dict[str, Any],
        await registry._client._request(
            "POST",
            "/admin/gql/strawberry",
            json={"query": _AUTHZ_QUERY, "variables": {"id": id_}},
        ),
    )
    assert result is not None, "Expected a non-null JSON response from the GQL endpoint"
    return result


class TestSharedDataLoaderCacheSharing:
    @pytest.mark.xfail(
        strict=True,
        reason="BA-6340: shared loader cache serves a foreign authorized result, bypassing load_fn",
    )
    async def test_authz_check_in_load_fn_is_enforced_per_request(
        self,
        server: Any,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        admin_user_fixture: Any,
    ) -> None:
        """An owner-only check inside load_fn must reject every unauthorized request.

        Currently FAILS: the shared cache serves admin's previously authorized result
        to a different user without re-running load_fn's check.
        """
        admin_id = str(admin_user_fixture.user_uuid)

        # admin loads its own id -> owner check passes inside load_fn, result cached.
        ok = await _authz_probe(admin_registry, admin_id)
        assert not ok.get("errors")
        assert ok["data"]["authzProbe"] == f"secret-of:{admin_id}"

        # a different user loads admin's id -> must be forbidden
        result = await _authz_probe(user_registry, admin_id)
        assert result.get("errors"), (
            "owner check must be enforced per request, not bypassed by cache"
        )
        data = result.get("data")
        assert data is None or data.get("authzProbe") is None

    @pytest.mark.xfail(
        strict=True,
        reason="BA-6340: a cached load_fn failure (negative caching) denies a later legitimate request",
    )
    async def test_cached_failure_does_not_deny_a_later_legitimate_request(
        self,
        server: Any,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        admin_user_fixture: Any,
    ) -> None:
        """A failed load must not poison the cache for a later legitimate request.

        Currently FAILS: a non-owner's forbidden load caches the exception, so the
        owner's own (should-succeed) load for the same id is denied from cache.
        """
        admin_id = str(admin_user_fixture.user_uuid)

        # a non-owner loads admin's id first -> correctly forbidden, exception cached.
        denied = await _authz_probe(user_registry, admin_id)
        assert denied.get("errors"), "non-owner load should be forbidden"

        # the owner loads its own id -> should succeed, but the cached failure denies it.
        owner = await _authz_probe(admin_registry, admin_id)
        assert not owner.get("errors"), "a cached failure must not deny the legitimate owner"
        assert owner["data"]["authzProbe"] == f"secret-of:{admin_id}"
