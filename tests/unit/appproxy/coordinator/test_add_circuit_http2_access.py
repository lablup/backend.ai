from __future__ import annotations

import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_mock

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    SessionConfig,
)
from ai.backend.appproxy.coordinator.errors.circuit import HTTP2AccessControlNotSupportedError
from ai.backend.appproxy.coordinator.models.worker import Worker, add_circuit


@dataclass(frozen=True)
class _CircuitAccessCase:
    worker_protocol: ProxyProtocol
    open_to_public: bool
    allowed_client_ips: str | None


class TestAddCircuitHTTP2Access:
    @pytest.fixture
    def stored_worker(self, case: _CircuitAccessCase, mocker: pytest_mock.MockerFixture) -> Worker:
        worker = Worker.create(
            uuid.uuid4(),
            "worker-1",
            FrontendMode.PORT,
            case.worker_protocol,
            "127.0.0.1",
            False,
            False,
            10200,
            [AppMode.INTERACTIVE],
            port_range=(10300, 10399),
        )
        worker.circuits = []
        mocker.patch(
            "ai.backend.appproxy.coordinator.models.worker.Worker.get",
            AsyncMock(return_value=worker),
        )
        return worker

    @pytest.fixture
    def session_config(self) -> SessionConfig:
        return SessionConfig(
            id=None,
            user_uuid=uuid.uuid4(),
            project_id=uuid.uuid4(),
            access_key=None,
            domain_name="default",
        )

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _CircuitAccessCase(
                    worker_protocol=ProxyProtocol.HTTP2,
                    open_to_public=True,
                    allowed_client_ips=None,
                ),
                id="http2_public_without_allowlist",
            ),
            pytest.param(
                _CircuitAccessCase(
                    worker_protocol=ProxyProtocol.HTTP,
                    open_to_public=False,
                    allowed_client_ips="10.0.0.0/8",
                ),
                id="http_private_with_allowlist",
            ),
        ],
    )
    async def test_circuit_is_created(
        self, case: _CircuitAccessCase, stored_worker: Worker, session_config: SessionConfig
    ) -> None:
        circuit, worker = await add_circuit(
            MagicMock(),
            session_config,
            None,
            "app",
            case.worker_protocol,
            AppMode.INTERACTIVE,
            [],
            open_to_public=case.open_to_public,
            allowed_client_ips=case.allowed_client_ips,
            worker_id=stored_worker.id,
        )

        assert circuit.open_to_public is case.open_to_public
        assert worker is stored_worker

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _CircuitAccessCase(
                    worker_protocol=ProxyProtocol.HTTP2,
                    open_to_public=False,
                    allowed_client_ips=None,
                ),
                id="http2_private",
            ),
            pytest.param(
                _CircuitAccessCase(
                    worker_protocol=ProxyProtocol.HTTP2,
                    open_to_public=True,
                    allowed_client_ips="10.0.0.0/8",
                ),
                id="http2_public_with_allowlist",
            ),
        ],
    )
    async def test_circuit_is_refused(
        self, case: _CircuitAccessCase, stored_worker: Worker, session_config: SessionConfig
    ) -> None:
        with pytest.raises(HTTP2AccessControlNotSupportedError):
            await add_circuit(
                MagicMock(),
                session_config,
                None,
                "app",
                case.worker_protocol,
                AppMode.INTERACTIVE,
                [],
                open_to_public=case.open_to_public,
                allowed_client_ips=case.allowed_client_ips,
                worker_id=stored_worker.id,
            )
