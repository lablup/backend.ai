"""Component regression tests: GraphQL DataLoaders are scoped to one request.

Every ``/admin/gql/strawberry`` request must execute with its own ``DataLoaders``
instance, so a value cached by one request's loader is never served to a later
request. These tests call a test-only probe field (defined in conftest, not in
the production schema) whose loader reads from a mutable in-memory store: a
store change made between two requests must be visible to the second request.

With a process-wide shared DataLoaders instance, the second request is served
the first request's cached value without re-reading the store, so every test
here fails deterministically.
"""

from __future__ import annotations

from typing import Any, cast

from ai.backend.client.v2.registry import BackendAIClientRegistry

_PROBE_QUERY = "query($key: String!) { probeCachedValue(key: $key) }"


async def _probe(
    registry: BackendAIClientRegistry,
    key: str,
) -> dict[str, Any]:
    """Query the probe field and return the raw GQL response."""
    result = await registry._client._request(
        "POST",
        "/admin/gql/strawberry",
        json={"query": _PROBE_QUERY, "variables": {"key": key}},
    )
    assert result is not None, "Expected a non-null JSON response from the GQL endpoint"
    return cast(dict[str, Any], result)


async def _probe_value(registry: BackendAIClientRegistry, key: str) -> int:
    """Query the probe field and return the loaded value, asserting no errors."""
    resp = await _probe(registry, key)
    assert not resp.get("errors"), f"Unexpected GQL errors: {resp.get('errors')}"
    return cast(int, resp["data"]["probeCachedValue"])


class TestPerRequestDataLoaderIsolation:
    async def test_update_between_requests_is_visible_to_the_next_request(
        self,
        admin_registry: BackendAIClientRegistry,
        loader_backing_store: dict[str, int],
        probe_key: str,
    ) -> None:
        """A value changed between two requests must be visible to the second.

        A loader cache shared across requests would serve the first request's
        cached value, so the second response would still carry the old one.
        """
        loader_backing_store[probe_key] = 1
        assert await _probe_value(admin_registry, probe_key) == 1

        loader_backing_store[probe_key] = 2
        assert await _probe_value(admin_registry, probe_key) == 2

    async def test_removal_between_requests_is_visible_to_the_next_request(
        self,
        admin_registry: BackendAIClientRegistry,
        loader_backing_store: dict[str, int],
        probe_key: str,
    ) -> None:
        """A value removed between two requests must not be served to the second.

        A loader cache shared across requests would keep serving the removed
        value from the first request's cache instead of failing.
        """
        loader_backing_store[probe_key] = 1
        assert await _probe_value(admin_registry, probe_key) == 1

        del loader_backing_store[probe_key]
        resp = await _probe(admin_registry, probe_key)
        assert resp.get("errors"), "a removed value must not be served from a previous request"

    async def test_load_failure_is_not_replayed_to_a_later_request(
        self,
        admin_registry: BackendAIClientRegistry,
        loader_backing_store: dict[str, int],
        probe_key: str,
    ) -> None:
        """A failed load in one request must not deny a later request.

        A loader cache shared across requests would cache the raised exception
        (negative caching) under the key and replay it to every later request.
        """
        failed = await _probe(admin_registry, probe_key)
        assert failed.get("errors"), "loading a missing key should fail"

        loader_backing_store[probe_key] = 3
        assert await _probe_value(admin_registry, probe_key) == 3
