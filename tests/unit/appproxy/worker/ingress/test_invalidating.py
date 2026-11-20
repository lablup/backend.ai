from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.invalidating import InvalidatingIngressWriter
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAuthority,
    IngressFrontendKey,
    IngressKey,
)

AUTHORITY = IngressAuthority("worker-1")
FRONTEND_KEY = IngressFrontendKey("port-10205")


@dataclass(frozen=True)
class _InvalidatedKeyAuthorityCase:
    invalidated_authority: IngressAuthority
    expected_held_keys: list[IngressFrontendKey]


@dataclass(frozen=True)
class _WriterOverAnIngressInMemory:
    writer: InvalidatingIngressWriter
    memory: InMemoryIngressState


@pytest.fixture
async def writer_over_an_ingress_in_memory() -> _WriterOverAnIngressInMemory:
    memory = InMemoryIngressState()
    await memory.apply([
        Ingress.model_validate({
            "id": "ingress-10205",
            "authority": AUTHORITY,
            "revision": 0,
            "frontend": {"kind": "port", "protocol": "http", "port": {"number": 10205}},
            "access": {"mode": "public", "allowed_client_ips": []},
            "backend": {
                "id": "backend-1",
                "target_groups": [{"id": "group-1", "weight": 1, "targets": []}],
            },
        })
    ])
    return _WriterOverAnIngressInMemory(
        writer=InvalidatingIngressWriter(memory, AUTHORITY), memory=memory
    )


class TestInvalidatingIngressWriter:
    @pytest.mark.parametrize(
        "case",
        [
            _InvalidatedKeyAuthorityCase(invalidated_authority=AUTHORITY, expected_held_keys=[]),
            _InvalidatedKeyAuthorityCase(
                invalidated_authority=IngressAuthority("worker-2"),
                expected_held_keys=[FRONTEND_KEY],
            ),
        ],
        ids=lambda case: case.invalidated_authority,
    )
    async def test_drops_only_the_keys_of_its_authority(
        self,
        case: _InvalidatedKeyAuthorityCase,
        writer_over_an_ingress_in_memory: _WriterOverAnIngressInMemory,
    ) -> None:
        await writer_over_an_ingress_in_memory.writer.apply([
            IngressKey(authority=case.invalidated_authority, frontend_key=FRONTEND_KEY)
        ])

        held_ingresses = await writer_over_an_ingress_in_memory.memory.get_all()
        assert [ingress.frontend.key() for ingress in held_ingresses] == case.expected_held_keys
