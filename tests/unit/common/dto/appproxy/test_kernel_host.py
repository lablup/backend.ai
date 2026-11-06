from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from ai.backend.common.dto.appproxy.kernel_host import KernelHost
from ai.backend.common.dto.appproxy.v2.ingress.types import SessionIngressTarget
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import RouteEntry
from ai.backend.common.types import SessionId

_SESSION_ID = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
_ROUTE_ID = UUID("4eeb260b-6cc5-4362-baf3-ea978388becd")


class TestKernelHost:
    @pytest.mark.parametrize(
        "kernel_host",
        [
            "10.0.0.1",
            "172.17.0.2",
            "192.168.1.100",
            "fd00::1",
            "127.0.0.1",
            "::1",
            "localhost",
            "agent-1.example.com",
            "agent_1",
        ],
    )
    def test_accepts_the_kernel_host(self, kernel_host: str) -> None:
        assert TypeAdapter(KernelHost).validate_python(kernel_host) == kernel_host

    @pytest.mark.parametrize(
        "kernel_host",
        [
            "169.254.169.254",
            "::ffff:169.254.169.254",
            "fe80::1",
            "2852039166",
            "169.254.43518",
            "0xa9.0xfe.0xa9.0xfe",
            "169.254.169.254.",
            "",
            "host name",
            "host/path",
            "user@host",
            "host:80",
            "10.0.0.1\nbackend=10.0.0.2,80",
        ],
    )
    def test_rejects_the_kernel_host(self, kernel_host: str) -> None:
        with pytest.raises(ValidationError):
            TypeAdapter(KernelHost).validate_python(kernel_host)


class TestModelsWithAKernelHost:
    def test_route_entry_rejects_a_metadata_address(self) -> None:
        with pytest.raises(ValidationError):
            RouteEntry(
                session_id=_SESSION_ID,
                route_id=_ROUTE_ID,
                kernel_host="169.254.169.254",
                kernel_port=80,
            )

    def test_session_ingress_target_rejects_a_metadata_address(self) -> None:
        with pytest.raises(ValidationError):
            SessionIngressTarget(
                host="169.254.169.254",
                port=80,
                session_id=SessionId(_SESSION_ID),
            )
