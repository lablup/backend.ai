"""Component tests for cross-request isolation of the shared ``DataLoaders`` instance.

These tests drive the real ``/admin/gql/strawberry`` endpoint (the ``loadedBatchIds``
probe backed by ``DataLoaders.loaded_batch_ids_loader``) with two concurrent requests
and assert the *desired* behavior: a request's load must only see its own key and run
in its own user context.

They are expected to FAIL against the current implementation, which shares a single
process-wide ``DataLoaders`` instance: concurrent loads coalesce into one batch that
runs in a single request's context. The probe ``load_fn`` echoes the coalesced batch
(and the user seen via ``current_user()``) back to each caller; an ``asyncio.Barrier``
(set on the shared ``DataLoaders`` in the ``data_loaders`` fixture) makes the coalescing
deterministic so the failure is reproducible rather than flaky.
"""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry

_PROBE_QUERY = "query($id: ID!) { loadedBatchIds(id: $id) { batch seenUser } }"


# ---------------------------------------------------------------------------
# GQL HTTP helper
# ---------------------------------------------------------------------------


async def _call_gql(
    registry: BackendAIClientRegistry,
    variables: dict[str, Any],
) -> dict[str, Any]:
    result = await registry._client._request(
        "POST",
        "/admin/gql/strawberry",
        json={"query": _PROBE_QUERY, "variables": variables},
    )
    assert result is not None, "Expected a non-null JSON response from the GQL endpoint"
    return cast(dict[str, Any], result)


def _payload(response: dict[str, Any]) -> dict[str, Any]:
    assert not response.get("errors"), f"Unexpected GQL errors: {response.get('errors')}"
    data = response.get("data")
    assert data is not None
    return cast(dict[str, Any], data["loadedBatchIds"])


# ---------------------------------------------------------------------------
# Tests (assert the desired isolation; currently FAIL due to the shared loader)
# ---------------------------------------------------------------------------


class TestSharedDataLoaderBatching:
    @pytest.mark.xfail(
        strict=True,
        reason="BA-6340: shared DataLoader coalesces cross-request loads (no per-request isolation)",
    )
    async def test_each_request_only_sees_its_own_load(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Each request's batch should contain only the key it loaded.

        Currently FAILS: the shared loader coalesces both requests' loads into one
        batch, so each response sees both ids.
        """
        id_a = "11111111-1111-1111-1111-111111111111"
        id_b = "22222222-2222-2222-2222-222222222222"

        resp_a, resp_b = await asyncio.wait_for(
            asyncio.gather(
                _call_gql(admin_registry, {"id": id_a}),
                _call_gql(user_registry, {"id": id_b}),
            ),
            timeout=10,
        )

        assert set(_payload(resp_a)["batch"]) == {id_a}
        assert set(_payload(resp_b)["batch"]) == {id_b}

    @pytest.mark.xfail(
        strict=True,
        reason="BA-6340: coalesced batch runs in a single request's context",
    )
    async def test_each_request_batch_runs_in_its_own_user_context(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Each request's load should run in its own user context.

        Currently FAILS: the coalesced batch runs in a single request's context, so
        both responses report the same user.
        """
        id_a = "33333333-3333-3333-3333-333333333333"
        id_b = "44444444-4444-4444-4444-444444444444"

        resp_a, resp_b = await asyncio.wait_for(
            asyncio.gather(
                _call_gql(admin_registry, {"id": id_a}),
                _call_gql(user_registry, {"id": id_b}),
            ),
            timeout=10,
        )

        seen_a = _payload(resp_a)["seenUser"]
        seen_b = _payload(resp_b)["seenUser"]
        assert seen_a is not None
        assert seen_b is not None
        assert seen_a != seen_b
