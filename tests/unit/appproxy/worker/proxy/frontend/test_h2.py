from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
import pytest_mock

from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol
from ai.backend.appproxy.worker.proxy.frontend.h2.port import PortFrontend
from ai.backend.appproxy.worker.types import Circuit, InteractiveAppInfo, PortFrontendInfo
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority, IngressFrontendKey

_WORKER_AUTHORITY = "worker-1"
_LISTEN_PORT = 10200
_API_PORT = 20000
_LISTEN_PORT_FRONTEND_KEY = IngressFrontendKey(f"port-{_LISTEN_PORT}")
_USER_ID = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")


@dataclass(frozen=True)
class _StoredCircuitCase:
    open_to_public: bool
    allowed_client_ips: str | None
    expected_frontend_keys: list[IngressFrontendKey]


@pytest.fixture
def root_context() -> MagicMock:
    root_ctx = MagicMock()
    root_ctx.local_config.proxy_worker.http2.api_port_pool = (_API_PORT, _API_PORT)
    return root_ctx


class TestRegisterIngress:
    @pytest.fixture
    def h2_frontend(
        self, root_context: MagicMock, mocker: pytest_mock.MockerFixture
    ) -> PortFrontend:
        mocker.patch(
            "ai.backend.appproxy.worker.proxy.frontend.h2.port.H2Backend.update_config",
            AsyncMock(),
        )
        frontend = PortFrontend(root_context)
        frontend.api_ports = {_LISTEN_PORT: _API_PORT}
        return frontend

    @pytest.fixture
    def stored_circuit(self, case: _StoredCircuitCase) -> Circuit:
        return Circuit(
            id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
            app="grpc-app",
            protocol=ProxyProtocol.HTTP2,
            worker=UUID("00000000-0000-0000-0000-000000000000"),
            app_mode=AppMode.INTERACTIVE,
            frontend_mode=FrontendMode.PORT,
            frontend=PortFrontendInfo(_LISTEN_PORT),
            port=_LISTEN_PORT,
            app_info=InteractiveAppInfo(user_id=_USER_ID),
            subdomain=None,
            runtime_variant=None,
            envs={},
            arguments=None,
            open_to_public=case.open_to_public,
            allowed_client_ips=case.allowed_client_ips,
            user_id=_USER_ID,
            access_key="AKIAIOSFODNN7EXAMPLE",
            endpoint_id=None,
            route_info=[],
            session_ids=[],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _StoredCircuitCase(
                    open_to_public=True,
                    allowed_client_ips=None,
                    expected_frontend_keys=[_LISTEN_PORT_FRONTEND_KEY],
                ),
                id="public_without_allowlist_is_registered",
            ),
            pytest.param(
                _StoredCircuitCase(
                    open_to_public=False,
                    allowed_client_ips=None,
                    expected_frontend_keys=[],
                ),
                id="private_is_skipped",
            ),
            pytest.param(
                _StoredCircuitCase(
                    open_to_public=True,
                    allowed_client_ips="10.0.0.0/8",
                    expected_frontend_keys=[],
                ),
                id="public_with_allowlist_is_skipped",
            ),
        ],
    )
    async def test_registered_frontend_keys(
        self, case: _StoredCircuitCase, h2_frontend: PortFrontend, stored_circuit: Circuit
    ) -> None:
        await h2_frontend.register_ingress(
            stored_circuit.to_ingress(IngressAuthority(_WORKER_AUTHORITY)), stored_circuit
        )

        assert list(h2_frontend.backends) == case.expected_frontend_keys
