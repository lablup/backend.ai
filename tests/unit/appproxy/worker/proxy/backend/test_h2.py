from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest
import pytest_mock
from aiohttp import web
from yarl import URL

from ai.backend.appproxy.worker.proxy.backend.h2 import H2Backend, H2BackendArgs
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
    PortFrontend,
    SessionIngressTarget,
)
from ai.backend.common.types import SessionId

_GROUP_ID = IngressTargetGroupID("00000000-0000-0000-0000-000000000000")
_BACKEND_ID = IngressBackendID("00000000-0000-0000-0000-000000000000")


@dataclass(frozen=True)
class _NghttpxAPISituation:
    backend: H2Backend
    received_backend_configs: list[str]


class TestH2Backend:
    @pytest.fixture
    async def h2_backend_with_an_nghttpx_api(
        self, aiohttp_server: Any, mocker: pytest_mock.MockerFixture
    ) -> _NghttpxAPISituation:
        received_backend_configs: list[str] = []

        async def receive_backend_config(request: web.Request) -> web.Response:
            received_backend_configs.append(await request.text())
            return web.Response()

        app = web.Application()
        app.router.add_post("/api/v1beta1/backendconfig", receive_backend_config)
        server = await aiohttp_server(app)
        backend = H2Backend(
            H2BackendArgs(
                last_used_time_marker_redis_queue=asyncio.Queue(),
                request_counter_redis_queue=asyncio.Queue(),
                ingress=mocker.MagicMock(),
                circuit=mocker.MagicMock(),
                api_endpoint=URL(f"http://{server.host}:{server.port}"),
            )
        )
        return _NghttpxAPISituation(
            backend=backend, received_backend_configs=received_backend_configs
        )

    async def test_update_sends_the_targets_of_every_group_as_nghttpx_backends(
        self, h2_backend_with_an_nghttpx_api: _NghttpxAPISituation
    ) -> None:
        situation = h2_backend_with_an_nghttpx_api
        await situation.backend.update_ingress(
            Ingress(
                id=IngressID("00000000-0000-0000-0000-000000000000"),
                authority=IngressAuthority("worker-1"),
                revision=0,
                frontend=IngressFrontend(
                    kind=IngressFrontendKind.PORT,
                    protocol=IngressProtocol.HTTP2,
                    port=PortFrontend(number=10200),
                ),
                access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
                backend=IngressBackend(
                    id=_BACKEND_ID,
                    target_groups=[
                        IngressTargetGroup(
                            id=_GROUP_ID,
                            weight=100,
                            targets=[
                                SessionIngressTarget(
                                    host="10.0.0.1",
                                    port=8000,
                                    session_id=SessionId(
                                        UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
                                    ),
                                )
                            ],
                        ),
                        IngressTargetGroup(
                            id=_GROUP_ID,
                            weight=50,
                            targets=[
                                SessionIngressTarget(
                                    host="10.0.0.2",
                                    port=8001,
                                    session_id=SessionId(
                                        UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
            )
        )
        assert situation.received_backend_configs == [
            "backend=10.0.0.1,8000;;proto=h2\nbackend=10.0.0.2,8001;;proto=h2"
        ]
