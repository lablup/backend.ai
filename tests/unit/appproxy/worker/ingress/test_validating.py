from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.appproxy.worker.errors.ingress import (
    IngressAuthorityMismatchError,
    IngressNotFoundError,
    IngressRevisionConflictError,
)
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.validating import ValidatingIngressWriter
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAuthority,
    IngressFrontendKey,
    IngressKey,
)

AUTHORITY = IngressAuthority("worker-1")


def _ingress(port: int, revision: int, authority: str = AUTHORITY) -> Ingress:
    return Ingress.model_validate({
        "id": f"ingress-{port}",
        "authority": authority,
        "revision": revision,
        "frontend": {"kind": "port", "protocol": "http", "port": {"number": port}},
        "access": {"mode": "public", "allowed_client_ips": []},
        "backend": {
            "id": "backend-1",
            "target_groups": [{"id": "group-1", "weight": 1, "targets": []}],
        },
    })


@pytest.fixture
def held() -> dict[IngressFrontendKey, Ingress]:
    return {IngressFrontendKey("10205"): _ingress(10205, revision=5)}


@pytest.fixture
def state(held: dict[IngressFrontendKey, Ingress]) -> AsyncMock:
    state = AsyncMock(spec=InMemoryIngressState)
    state.get.side_effect = lambda key: held.get(key)
    return state


@pytest.fixture
def writer(state: AsyncMock) -> ValidatingIngressWriter:
    return ValidatingIngressWriter(state, AUTHORITY)


class TestValidatingIngressWriter:
    async def test_newer_revision_is_applied(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        ingresses = [_ingress(10205, revision=6)]
        await writer.apply(ingresses)
        state.apply.assert_awaited_once_with(ingresses)

    async def test_same_revision_is_applied(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        ingresses = [_ingress(10205, revision=5)]
        await writer.apply(ingresses)
        state.apply.assert_awaited_once_with(ingresses)

    async def test_key_not_held_is_applied(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        ingresses = [_ingress(10206, revision=0)]
        await writer.apply(ingresses)
        state.apply.assert_awaited_once_with(ingresses)

    async def test_key_remembered_missing_is_applied(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        state.get.side_effect = IngressNotFoundError
        ingresses = [_ingress(10206, revision=0)]
        await writer.apply(ingresses)
        state.apply.assert_awaited_once_with(ingresses)

    async def test_older_revision_rejects_the_whole_apply(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        with pytest.raises(IngressRevisionConflictError):
            await writer.apply([_ingress(10206, revision=0), _ingress(10205, revision=4)])
        state.apply.assert_not_awaited()

    async def test_other_authority_rejects_the_whole_apply(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        with pytest.raises(IngressAuthorityMismatchError):
            await writer.apply([
                _ingress(10206, revision=0),
                _ingress(10207, revision=0, authority="worker-2"),
            ])
        state.apply.assert_not_awaited()

    async def test_other_authority_rejects_replace_all(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        with pytest.raises(IngressAuthorityMismatchError):
            await writer.replace_all([_ingress(10205, revision=1, authority="worker-2")])
        state.replace_all.assert_not_awaited()

    async def test_remove_is_delegated(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        keys = [IngressKey(authority=AUTHORITY, frontend_key=IngressFrontendKey("10205"))]
        await writer.remove(keys)
        state.remove.assert_awaited_once_with(keys)

    async def test_other_authority_rejects_remove(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        with pytest.raises(IngressAuthorityMismatchError):
            await writer.remove([
                IngressKey(
                    authority=IngressAuthority("worker-2"), frontend_key=IngressFrontendKey("10205")
                )
            ])
        state.remove.assert_not_awaited()

    async def test_replace_all_is_delegated_without_comparing(
        self, writer: ValidatingIngressWriter, state: AsyncMock
    ) -> None:
        ingresses = [_ingress(10205, revision=1)]
        await writer.replace_all(ingresses)
        state.replace_all.assert_awaited_once_with(ingresses)
