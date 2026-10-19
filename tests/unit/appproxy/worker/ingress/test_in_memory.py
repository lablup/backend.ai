from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest

from ai.backend.appproxy.worker.errors.ingress import IngressNotFoundError
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressBackend,
    IngressBackendID,
    IngressFrontend,
    IngressFrontendKey,
    IngressFrontendKind,
    IngressID,
    IngressKey,
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)

AUTHORITY = IngressAuthority("worker-1")
STORED_KEY = IngressFrontendKey("10205")
OTHER_KEY = IngressFrontendKey("10206")
STARTED_AT = 1000.0
TTL = 60.0
NEGATIVE_TTL = 5.0


@dataclass(frozen=True)
class _ElapsedCase:
    elapsed: float
    stored: bool


@dataclass(frozen=True)
class _HeldCase:
    applied_revision: int
    held_revision: int


@dataclass(frozen=True)
class _ApplyCase:
    applied_after: float
    applied_revision: int
    read_after: float
    read_revision: int


@pytest.fixture
def clock() -> Iterator[Mock]:
    with patch(
        "ai.backend.appproxy.worker.ingress.in_memory.monotonic", return_value=STARTED_AT
    ) as clock:
        yield clock


@pytest.fixture
def stored_ingress() -> Ingress:
    return Ingress(
        id=IngressID("ingress-10205"),
        authority=AUTHORITY,
        revision=5,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=10205),
        ),
        access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
        backend=IngressBackend(
            id=IngressBackendID("backend-1"),
            target_groups=[
                IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
            ],
        ),
    )


@pytest.fixture
def other_ingress() -> Ingress:
    return Ingress(
        id=IngressID("ingress-10206"),
        authority=AUTHORITY,
        revision=0,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=10206),
        ),
        access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
        backend=IngressBackend(
            id=IngressBackendID("backend-2"),
            target_groups=[
                IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
            ],
        ),
    )


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
            _ApplyCase(applied_after=10, applied_revision=6, read_after=10, read_revision=6),
            _ApplyCase(applied_after=10, applied_revision=5, read_after=10, read_revision=5),
            _ApplyCase(applied_after=10, applied_revision=4, read_after=10, read_revision=5),
            _ApplyCase(
                applied_after=TTL - 10, applied_revision=5, read_after=TTL + 10, read_revision=5
            ),
            _ApplyCase(
                applied_after=TTL + 1, applied_revision=4, read_after=TTL + 1, read_revision=4
            ),
        ],
        ids=lambda case: (
            f"revision-{case.applied_revision}-applied-at-{case.applied_after:g}"
            f"-read-at-{case.read_after:g}"
        ),
    )
    async def test_apply_stores_unless_a_newer_revision_is_still_stored(
        self,
        expiring_state: InMemoryIngressState,
        clock: Mock,
        stored_ingress: Ingress,
        case: _ApplyCase,
    ) -> None:
        clock.return_value = STARTED_AT + case.applied_after
        await expiring_state.apply([
            stored_ingress.model_copy(update={"revision": case.applied_revision})
        ])
        clock.return_value = STARTED_AT + case.read_after
        read_back_ingress = await expiring_state.get(STORED_KEY)
        assert read_back_ingress is not None
        assert read_back_ingress.revision == case.read_revision

    @pytest.mark.parametrize(
        "case",
        [
            _HeldCase(applied_revision=6, held_revision=6),
            _HeldCase(applied_revision=5, held_revision=5),
            _HeldCase(applied_revision=4, held_revision=5),
        ],
        ids=lambda case: f"revision-{case.applied_revision}",
    )
    async def test_apply_returns_the_held_ingress(
        self, state: InMemoryIngressState, stored_ingress: Ingress, case: _HeldCase
    ) -> None:
        [held_ingress] = await state.apply([
            stored_ingress.model_copy(update={"revision": case.applied_revision})
        ])
        assert held_ingress.revision == case.held_revision

    async def test_apply_stores_a_new_key(
        self, state: InMemoryIngressState, other_ingress: Ingress
    ) -> None:
        await state.apply([other_ingress])
        assert await state.get(OTHER_KEY) == other_ingress

    async def test_remove_drops_the_key(self, state: InMemoryIngressState) -> None:
        await state.remove([IngressKey(authority=AUTHORITY, frontend_key=STORED_KEY)])
        assert await state.get(STORED_KEY) is None

    async def test_removed_key_is_remembered_missing(
        self, negative_caching_state: InMemoryIngressState
    ) -> None:
        await negative_caching_state.remove([
            IngressKey(authority=AUTHORITY, frontend_key=STORED_KEY)
        ])
        with pytest.raises(IngressNotFoundError):
            await negative_caching_state.get(STORED_KEY)

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

    async def test_replace_all_returns_every_held_ingress(
        self, state: InMemoryIngressState, other_ingress: Ingress
    ) -> None:
        assert await state.replace_all([other_ingress]) == [other_ingress]

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
        assert (len(await expiring_state.get_all()) == 1) is case.stored

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
