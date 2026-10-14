from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest

from ai.backend.appproxy.worker.errors.ingress import IngressNotFoundError
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAuthority,
    IngressFrontendKey,
    IngressKey,
)

AUTHORITY = IngressAuthority("worker-1")
STORED_KEY = IngressFrontendKey("10205")
OTHER_KEY = IngressFrontendKey("10206")
STARTED_AT = 1000.0
TTL = 60.0
NEGATIVE_TTL = 5.0


@dataclass(frozen=True)
class _RevisionCase:
    incoming_revision: int
    stored_revision: int


@dataclass(frozen=True)
class _ElapsedCase:
    elapsed: float
    stored: bool


@pytest.fixture
def clock() -> Iterator[Mock]:
    with patch(
        "ai.backend.appproxy.worker.ingress.in_memory.monotonic", return_value=STARTED_AT
    ) as clock:
        yield clock


@pytest.fixture
def stored_ingress() -> Ingress:
    return Ingress.model_validate({
        "id": "ingress-10205",
        "authority": AUTHORITY,
        "revision": 5,
        "frontend": {"kind": "port", "protocol": "http", "port": {"number": 10205}},
        "access": {"mode": "public", "allowed_client_ips": []},
        "backend": {
            "id": "backend-1",
            "target_groups": [{"id": "group-1", "weight": 1, "targets": []}],
        },
    })


@pytest.fixture
def other_ingress() -> Ingress:
    return Ingress.model_validate({
        "id": "ingress-10206",
        "authority": AUTHORITY,
        "revision": 0,
        "frontend": {"kind": "port", "protocol": "http", "port": {"number": 10206}},
        "access": {"mode": "public", "allowed_client_ips": []},
        "backend": {
            "id": "backend-2",
            "target_groups": [{"id": "group-1", "weight": 1, "targets": []}],
        },
    })


@pytest.fixture
def state(clock: Mock, stored_ingress: Ingress) -> InMemoryIngressState:
    state = InMemoryIngressState()
    state._ingresses[STORED_KEY] = stored_ingress
    return state


@pytest.fixture
def expiring_state(clock: Mock, stored_ingress: Ingress) -> InMemoryIngressState:
    state = InMemoryIngressState(ttl=TTL)
    state._ingresses[STORED_KEY] = stored_ingress
    return state


@pytest.fixture
def negative_caching_state(clock: Mock, stored_ingress: Ingress) -> InMemoryIngressState:
    state = InMemoryIngressState(negative_ttl=NEGATIVE_TTL)
    state._ingresses[STORED_KEY] = stored_ingress
    state._missing_keys[OTHER_KEY] = True
    return state


class TestInMemoryIngressState:
    async def test_get_returns_the_stored_ingress(
        self, state: InMemoryIngressState, stored_ingress: Ingress
    ) -> None:
        assert await state.get(STORED_KEY) == stored_ingress

    async def test_get_returns_none_for_a_key_never_stored(
        self, state: InMemoryIngressState
    ) -> None:
        assert await state.get(OTHER_KEY) is None

    async def test_get_all_returns_every_stored_ingress(
        self, state: InMemoryIngressState, stored_ingress: Ingress
    ) -> None:
        assert await state.get_all() == [stored_ingress]

    @pytest.mark.parametrize(
        "case",
        [
            _RevisionCase(incoming_revision=6, stored_revision=6),
            _RevisionCase(incoming_revision=5, stored_revision=5),
            _RevisionCase(incoming_revision=4, stored_revision=5),
        ],
        ids=lambda case: f"incoming-{case.incoming_revision}",
    )
    async def test_apply_never_overwrites_a_newer_revision(
        self, state: InMemoryIngressState, stored_ingress: Ingress, case: _RevisionCase
    ) -> None:
        await state.apply([stored_ingress.model_copy(update={"revision": case.incoming_revision})])
        read_back_ingress = await state.get(STORED_KEY)
        assert read_back_ingress is not None
        assert read_back_ingress.revision == case.stored_revision

    async def test_apply_stores_a_new_key(
        self, state: InMemoryIngressState, other_ingress: Ingress
    ) -> None:
        await state.apply([other_ingress])
        assert await state.get(OTHER_KEY) == other_ingress

    async def test_remove_drops_the_key(self, state: InMemoryIngressState) -> None:
        await state.remove([IngressKey(authority=AUTHORITY, frontend_key=STORED_KEY)])
        assert await state.get(STORED_KEY) is None

    async def test_remove_ignores_a_key_not_stored(
        self, state: InMemoryIngressState, stored_ingress: Ingress
    ) -> None:
        await state.remove([IngressKey(authority=AUTHORITY, frontend_key=OTHER_KEY)])
        assert await state.get_all() == [stored_ingress]

    async def test_replace_all_swaps_every_stored_ingress(
        self, state: InMemoryIngressState, other_ingress: Ingress
    ) -> None:
        await state.replace_all([other_ingress])
        assert await state.get_all() == [other_ingress]

    async def test_replace_all_with_nothing_clears_every_stored_ingress(
        self, state: InMemoryIngressState
    ) -> None:
        await state.replace_all([])
        assert await state.get_all() == []

    @pytest.mark.parametrize(
        "case",
        [
            _ElapsedCase(elapsed=TTL - 1, stored=True),
            _ElapsedCase(elapsed=TTL + 1, stored=False),
        ],
        ids=lambda case: f"elapsed-{case.elapsed:g}",
    )
    async def test_ingress_is_stored_until_ttl_passes(
        self, expiring_state: InMemoryIngressState, clock: Mock, case: _ElapsedCase
    ) -> None:
        clock.return_value = STARTED_AT + case.elapsed
        assert (await expiring_state.get(STORED_KEY) is not None) is case.stored

    async def test_get_all_leaves_out_an_expired_ingress(
        self, expiring_state: InMemoryIngressState, clock: Mock
    ) -> None:
        clock.return_value = STARTED_AT + TTL + 1
        assert await expiring_state.get_all() == []

    async def test_reapplied_ingress_is_stored_for_a_new_ttl(
        self, expiring_state: InMemoryIngressState, clock: Mock, stored_ingress: Ingress
    ) -> None:
        clock.return_value = STARTED_AT + TTL - 10
        await expiring_state.apply([stored_ingress])
        clock.return_value = STARTED_AT + TTL + 10
        assert await expiring_state.get(STORED_KEY) == stored_ingress

    async def test_apply_stores_an_older_revision_once_the_stored_one_expires(
        self, expiring_state: InMemoryIngressState, clock: Mock, stored_ingress: Ingress
    ) -> None:
        clock.return_value = STARTED_AT + TTL + 1
        older = stored_ingress.model_copy(update={"revision": 4})
        await expiring_state.apply([older])
        assert await expiring_state.get(STORED_KEY) == older

    async def test_get_raises_for_a_key_remembered_missing(
        self, negative_caching_state: InMemoryIngressState, clock: Mock
    ) -> None:
        clock.return_value = STARTED_AT + NEGATIVE_TTL - 1
        with pytest.raises(IngressNotFoundError):
            await negative_caching_state.get(OTHER_KEY)

    async def test_missing_mark_expires_after_negative_ttl(
        self, negative_caching_state: InMemoryIngressState, clock: Mock
    ) -> None:
        clock.return_value = STARTED_AT + NEGATIVE_TTL + 1
        assert await negative_caching_state.get(OTHER_KEY) is None

    async def test_remember_missing_marks_the_key(
        self, negative_caching_state: InMemoryIngressState
    ) -> None:
        key = IngressFrontendKey("10207")
        await negative_caching_state.remember_missing(key)
        with pytest.raises(IngressNotFoundError):
            await negative_caching_state.get(key)

    async def test_apply_clears_the_missing_mark(
        self, negative_caching_state: InMemoryIngressState, other_ingress: Ingress
    ) -> None:
        await negative_caching_state.apply([other_ingress])
        assert await negative_caching_state.get(OTHER_KEY) == other_ingress

    async def test_stored_ingress_wins_over_a_later_missing_mark(
        self, negative_caching_state: InMemoryIngressState, stored_ingress: Ingress
    ) -> None:
        await negative_caching_state.remember_missing(STORED_KEY)
        assert await negative_caching_state.get(STORED_KEY) == stored_ingress

    async def test_remember_missing_without_negative_ttl_is_ignored(
        self, state: InMemoryIngressState
    ) -> None:
        await state.remember_missing(OTHER_KEY)
        assert await state.get(OTHER_KEY) is None
