from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
import pytest_mock

from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.proxy.frontend.tcp import TCPFrontend
from ai.backend.appproxy.worker.types import Circuit, InferenceAppInfo, PortFrontendInfo
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAuthority,
)

_AUTHORITY = IngressAuthority("worker-1")
_PORT = 10200
_SESSION_ID = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
_ENDPOINT_ID = UUID("2b8e4f1a-3c5d-4e6f-8a9b-0c1d2e3f4a5b")
_NEW_ROUTE_ID = UUID("7c1b6a52-2f0e-4d8a-9a3e-5b1d2c6f4e80")


@dataclass(frozen=True)
class _IngressUpdateSituation:
    frontend: TCPFrontend
    backend: MagicMock
    updated_ingress: Ingress


class TestBaseFrontend:
    @pytest.fixture
    def frontend_holding_a_backend_of_an_updated_ingress(
        self, mocker: pytest_mock.MockerFixture
    ) -> _IngressUpdateSituation:
        held_circuit = Circuit(
            id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
            app="vllm",
            protocol=ProxyProtocol.TCP,
            worker=UUID("00000000-0000-0000-0000-000000000000"),
            app_mode=AppMode.INFERENCE,
            frontend_mode=FrontendMode.PORT,
            frontend=PortFrontendInfo(_PORT),
            port=_PORT,
            app_info=InferenceAppInfo(endpoint_id=_ENDPOINT_ID, runtime_variant=None),
            subdomain=None,
            runtime_variant=None,
            envs={},
            arguments=None,
            open_to_public=True,
            allowed_client_ips=None,
            user_id=None,
            access_key=None,
            endpoint_id=_ENDPOINT_ID,
            route_info=[
                RouteInfo(
                    route_id=UUID("4eeb260b-6cc5-4362-baf3-ea978388becd"),
                    session_id=_SESSION_ID,
                    session_name=None,
                    kernel_host="10.0.0.1",
                    kernel_port=8000,
                    protocol=ProxyProtocol.TCP,
                    traffic_ratio=1.0,
                )
            ],
            session_ids=[_SESSION_ID],
            created_at=datetime(2024, 7, 16, tzinfo=UTC),
            updated_at=datetime(2024, 7, 16, tzinfo=UTC),
        )
        new_route = RouteInfo(
            route_id=_NEW_ROUTE_ID,
            session_id=_SESSION_ID,
            session_name=None,
            kernel_host="10.0.0.2",
            kernel_port=8001,
            protocol=ProxyProtocol.TCP,
            traffic_ratio=1.0,
        )
        frontend = TCPFrontend(mocker.MagicMock())
        backend = mocker.MagicMock(update_ingress=AsyncMock())
        frontend.backends[held_circuit.to_ingress_frontend().key()] = backend
        return _IngressUpdateSituation(
            frontend=frontend,
            backend=backend,
            updated_ingress=held_circuit.model_copy(update={"route_info": [new_route]}).to_ingress(
                _AUTHORITY
            ),
        )

    async def test_update_hands_the_backend_the_targets_of_the_updated_ingress(
        self, frontend_holding_a_backend_of_an_updated_ingress: _IngressUpdateSituation
    ) -> None:
        situation = frontend_holding_a_backend_of_an_updated_ingress
        await situation.frontend.update_ingress(situation.updated_ingress)
        situation.backend.update_ingress.assert_awaited_once_with(situation.updated_ingress)
