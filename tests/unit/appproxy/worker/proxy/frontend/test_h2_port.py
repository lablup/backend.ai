from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from unittest.mock import ANY, AsyncMock, MagicMock
from uuid import UUID

import pytest
import pytest_mock

from ai.backend.appproxy.worker.proxy.backend.h2 import BackendConfig, H2Backend
from ai.backend.appproxy.worker.proxy.frontend.h2.port import PortFrontend
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressBackend,
    IngressBackendID,
    IngressFrontend,
    IngressFrontendKind,
    IngressID,
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    SessionIngressTarget,
)
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    PortFrontend as IngressPortFrontend,
)
from ai.backend.common.types import SessionId

_BIND_HOST = "192.0.2.1"
_LISTEN_PORT = 10200
_API_PORT = 20000


def _port_ingress(target_groups: list[IngressTargetGroup]) -> Ingress:
    return Ingress(
        id=IngressID(str(UUID(int=0))),
        authority=IngressAuthority("worker-1"),
        revision=0,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP2,
            port=IngressPortFrontend(number=_LISTEN_PORT),
        ),
        access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
        backend=IngressBackend(id=IngressBackendID(str(UUID(int=0))), target_groups=target_groups),
    )


@dataclass(frozen=True)
class _H2FrontendServingAnIngress:
    frontend: PortFrontend
    ingress_with_targets_with_and_without_traffic: Ingress
    update_nghttpx_config: AsyncMock


class TestStart:
    @pytest.fixture
    async def nghttpx_exec_of_started_no_tls_frontend(
        self, mocker: pytest_mock.MockerFixture
    ) -> AsyncIterator[AsyncMock]:
        root_context = MagicMock()
        worker_config = root_context.local_config.proxy_worker
        worker_config.tls_listen = False
        worker_config.http2.api_port_pool = (_API_PORT, _API_PORT)
        worker_config.port_proxy.bind_host = _BIND_HOST
        worker_config.port_proxy.bind_port_range = (_LISTEN_PORT, _LISTEN_PORT)
        nghttpx_stream = MagicMock(readline=AsyncMock(return_value=b""))
        create_subprocess_exec = mocker.patch(
            "ai.backend.appproxy.worker.proxy.frontend.h2.port.subprocess.create_subprocess_exec",
            AsyncMock(
                return_value=MagicMock(
                    stdout=nghttpx_stream, stderr=nghttpx_stream, wait=AsyncMock()
                )
            ),
        )
        frontend = PortFrontend(root_context)
        frontend.proc_monitor_tasks = []
        frontend.log_monitor_tasks = []
        await frontend.start()
        yield create_subprocess_exec
        await asyncio.gather(*frontend.proc_monitor_tasks, *frontend.log_monitor_tasks)

    async def test_nghttpx_listens_on_the_bind_host_without_tls(
        self, nghttpx_exec_of_started_no_tls_frontend: AsyncMock
    ) -> None:
        assert (
            f"--frontend={_BIND_HOST},{_LISTEN_PORT};no-tls"
            in nghttpx_exec_of_started_no_tls_frontend.call_args.args
        )


class TestIngressUpdate:
    @pytest.fixture
    async def h2_frontend_serving_an_ingress(
        self, mocker: pytest_mock.MockerFixture
    ) -> _H2FrontendServingAnIngress:
        root_context = MagicMock()
        root_context.local_config.proxy_worker.http2.api_port_pool = (_API_PORT, _API_PORT)
        update_nghttpx_config = mocker.patch.object(H2Backend, "update_config", autospec=True)
        frontend = PortFrontend(root_context)
        frontend.api_ports = {_LISTEN_PORT: _API_PORT}
        served_ingress = _port_ingress([
            IngressTargetGroup(
                id=IngressTargetGroupID(str(UUID(int=0))),
                weight=1,
                targets=[
                    SessionIngressTarget(
                        host="10.0.0.1",
                        port=30001,
                        session_id=SessionId(UUID("3f2b8c1a-6d4e-4f7a-9b0c-1d2e3f4a5b6c")),
                    )
                ],
            )
        ])
        frontend.backends[served_ingress.frontend.key()] = await frontend.initialize_backend(
            served_ingress
        )
        update_nghttpx_config.reset_mock()
        return _H2FrontendServingAnIngress(
            frontend=frontend,
            ingress_with_targets_with_and_without_traffic=_port_ingress([
                IngressTargetGroup(
                    id=IngressTargetGroupID(str(UUID(int=0))),
                    weight=1,
                    targets=[
                        SessionIngressTarget(
                            host="10.0.0.2",
                            port=30002,
                            session_id=SessionId(UUID("8a7b6c5d-4e3f-4a1b-9c8d-7e6f5a4b3c2d")),
                        )
                    ],
                ),
                IngressTargetGroup(
                    id=IngressTargetGroupID(str(UUID(int=1))),
                    weight=0,
                    targets=[
                        SessionIngressTarget(
                            host="10.0.0.3",
                            port=30003,
                            session_id=SessionId(UUID("1c2d3e4f-5a6b-4c7d-8e9f-0a1b2c3d4e5f")),
                        )
                    ],
                ),
            ]),
            update_nghttpx_config=update_nghttpx_config,
        )

    async def test_update_sends_every_target_to_nghttpx(
        self, h2_frontend_serving_an_ingress: _H2FrontendServingAnIngress
    ) -> None:
        situation = h2_frontend_serving_an_ingress
        await situation.frontend.update_ingress(
            situation.ingress_with_targets_with_and_without_traffic
        )

        situation.update_nghttpx_config.assert_awaited_once_with(
            ANY,
            [BackendConfig("10.0.0.2", 30002), BackendConfig("10.0.0.3", 30003)],
        )
