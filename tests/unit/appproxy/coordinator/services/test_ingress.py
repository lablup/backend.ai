from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, Mock

import aiohttp
import pytest

from ai.backend.appproxy.common.config import SecretConfig
from ai.backend.appproxy.common.defs import (
    WORKER_AUTHORITY_LABEL,
    WORKER_INGRESS_DELIVERY_MODE_LABEL,
    WORKER_SERVICE_GROUP,
)
from ai.backend.appproxy.common.types import IngressDeliveryMode
from ai.backend.appproxy.coordinator.errors.ingress import (
    ApiDeliveryWorkerPushFailedError,
    ApiDeliveryWorkerServerError,
    ApiDeliveryWorkerUnreachableError,
)
from ai.backend.appproxy.coordinator.services.ingress import IngressService
from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.dto.appproxy.v2.ingress.request import (
    IngressRemoveRequest,
    IngressUpsertRequest,
)
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
    IngressKey,
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceEndpoint,
    ServiceMetadata,
)

WORKER_1_NODE_A = "10.0.0.1:10201"
WORKER_1_NODE_B = "10.0.0.2:10201"
WORKER_1_REDIS_NODE = "10.0.0.3:10201"
WORKER_2_NODE = "10.0.1.1:10201"


@dataclass(frozen=True)
class _PushOperationCase:
    name: str
    push: Callable[[IngressService, Ingress], Awaitable[None]]


@dataclass(frozen=True)
class _PushFailure:
    worker_addr: str
    error_type: str


def _node(authority: str, delivery_mode: IngressDeliveryMode, addr: str) -> ServiceMetadata:
    host, port = addr.split(":")
    return ServiceMetadata.for_endpoint(
        display_name=f"appproxy-worker-{authority}",
        service_group=WORKER_SERVICE_GROUP,
        version="test",
        endpoint=ServiceEndpoint(
            address=host, port=int(port), protocol="http", prometheus_address=addr
        ),
        labels={
            WORKER_AUTHORITY_LABEL: authority,
            WORKER_INGRESS_DELIVERY_MODE_LABEL: delivery_mode,
        },
    )


@pytest.fixture
def public_access() -> IngressAccess:
    return IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[])


@pytest.fixture
def backend() -> IngressBackend:
    return IngressBackend(
        id=IngressBackendID("backend-1"),
        target_groups=[
            IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
        ],
    )


@pytest.fixture
def worker_1_ingress(public_access: IngressAccess, backend: IngressBackend) -> Ingress:
    return Ingress(
        id=IngressID("ingress-10205"),
        authority=IngressAuthority("worker-1"),
        revision=3,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=10205),
        ),
        access=public_access,
        backend=backend,
    )


@pytest.fixture
def worker_2_ingress(public_access: IngressAccess, backend: IngressBackend) -> Ingress:
    return Ingress(
        id=IngressID("ingress-10206"),
        authority=IngressAuthority("worker-2"),
        revision=5,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=10206),
        ),
        access=public_access,
        backend=backend,
    )


@pytest.fixture
def unannounced_ingress(public_access: IngressAccess, backend: IngressBackend) -> Ingress:
    return Ingress(
        id=IngressID("ingress-10207"),
        authority=IngressAuthority("worker-3"),
        revision=1,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=10207),
        ),
        access=public_access,
        backend=backend,
    )


@pytest.fixture
def service_discovery() -> AsyncMock:
    service_discovery = AsyncMock(spec=ServiceDiscovery)
    service_discovery.get_service_group.return_value = [
        _node("worker-1", IngressDeliveryMode.API, WORKER_1_NODE_A),
        _node("worker-1", IngressDeliveryMode.API, WORKER_1_NODE_B),
        _node("worker-1", IngressDeliveryMode.REDIS, WORKER_1_REDIS_NODE),
        _node("worker-2", IngressDeliveryMode.API, WORKER_2_NODE),
    ]
    return service_discovery


@pytest.fixture
def empty_service_discovery() -> AsyncMock:
    service_discovery = AsyncMock(spec=ServiceDiscovery)
    service_discovery.get_service_group.side_effect = ValueError("No services found")
    return service_discovery


@pytest.fixture
def secrets() -> SecretConfig:
    return SecretConfig(api_secret="api-secret", jwt_secret="jwt-secret")


@pytest.fixture
def worker_sessions() -> dict[str, MagicMock]:
    sessions: dict[str, MagicMock] = {}
    for addr in (WORKER_1_NODE_A, WORKER_1_NODE_B, WORKER_1_REDIS_NODE, WORKER_2_NODE):
        response = MagicMock()
        response.status = 200
        response.read = AsyncMock(return_value=b"")
        session = MagicMock()
        session.post.return_value.__aenter__.return_value = response
        sessions[addr] = session
    return sessions


@pytest.fixture
def failing_node(worker_sessions: dict[str, MagicMock]) -> dict[str, MagicMock]:
    worker_sessions[WORKER_1_NODE_A].post.side_effect = aiohttp.ClientConnectionError(
        "connection refused"
    )
    return worker_sessions


@pytest.fixture
def server_error_node(failing_node: dict[str, MagicMock]) -> dict[str, MagicMock]:
    response = failing_node[WORKER_1_NODE_B].post.return_value.__aenter__.return_value
    response.status = HTTPStatus.INTERNAL_SERVER_ERROR
    return failing_node


@pytest.fixture
def slow_node_finished(worker_sessions: dict[str, MagicMock]) -> asyncio.Event:
    finished = asyncio.Event()

    async def read_after_a_delay() -> bytes:
        await asyncio.sleep(0.05)
        finished.set()
        return b""

    response = worker_sessions[WORKER_1_NODE_B].post.return_value.__aenter__.return_value
    response.read.side_effect = read_after_a_delay
    return finished


@pytest.fixture
def client_pool(worker_sessions: dict[str, MagicMock]) -> Mock:
    sessions = {f"http://{addr}": session for addr, session in worker_sessions.items()}
    client_pool = Mock(spec=ClientPool)
    client_pool.load_client_session.side_effect = lambda key: sessions[key.endpoint]
    return client_pool


@pytest.fixture
def service(
    service_discovery: AsyncMock, client_pool: Mock, secrets: SecretConfig
) -> IngressService:
    return IngressService(service_discovery, client_pool, secrets, traefik_writer=None)


class TestIngressService:
    async def test_upsert_pushes_each_authority_to_its_api_nodes(
        self,
        service: IngressService,
        worker_sessions: dict[str, MagicMock],
        worker_1_ingress: Ingress,
        worker_2_ingress: Ingress,
    ) -> None:
        await service.upsert([worker_1_ingress, worker_2_ingress])
        pushed = {
            addr: tuple(
                ingress.key()
                for ingress in IngressUpsertRequest.model_validate(
                    session.post.call_args.kwargs["json"]
                ).ingresses
            )
            for addr, session in worker_sessions.items()
            if session.post.call_args is not None
        }
        assert pushed == {
            WORKER_1_NODE_A: (worker_1_ingress.key(),),
            WORKER_1_NODE_B: (worker_1_ingress.key(),),
            WORKER_2_NODE: (worker_2_ingress.key(),),
        }

    async def test_remove_pushes_each_authority_to_its_api_nodes(
        self,
        service: IngressService,
        worker_sessions: dict[str, MagicMock],
        worker_1_ingress: Ingress,
        worker_2_ingress: Ingress,
    ) -> None:
        await service.remove([worker_1_ingress.key(), worker_2_ingress.key()])
        pushed: dict[str, tuple[IngressKey, ...]] = {
            addr: tuple(
                IngressRemoveRequest.model_validate(session.post.call_args.kwargs["json"]).keys
            )
            for addr, session in worker_sessions.items()
            if session.post.call_args is not None
        }
        assert pushed == {
            WORKER_1_NODE_A: (worker_1_ingress.key(),),
            WORKER_1_NODE_B: (worker_1_ingress.key(),),
            WORKER_2_NODE: (worker_2_ingress.key(),),
        }

    async def test_authority_without_an_api_node_is_skipped(
        self,
        service: IngressService,
        worker_sessions: dict[str, MagicMock],
        worker_1_ingress: Ingress,
        unannounced_ingress: Ingress,
    ) -> None:
        await service.upsert([worker_1_ingress, unannounced_ingress])
        pushed = {
            addr: tuple(
                ingress.key()
                for ingress in IngressUpsertRequest.model_validate(
                    session.post.call_args.kwargs["json"]
                ).ingresses
            )
            for addr, session in worker_sessions.items()
            if session.post.call_args is not None
        }
        assert pushed == {
            WORKER_1_NODE_A: (worker_1_ingress.key(),),
            WORKER_1_NODE_B: (worker_1_ingress.key(),),
        }

    async def test_no_registered_worker_pushes_nothing(
        self,
        empty_service_discovery: AsyncMock,
        client_pool: Mock,
        secrets: SecretConfig,
        worker_sessions: dict[str, MagicMock],
        worker_1_ingress: Ingress,
    ) -> None:
        service = IngressService(empty_service_discovery, client_pool, secrets, traefik_writer=None)
        await service.upsert([worker_1_ingress])
        for session in worker_sessions.values():
            session.post.assert_not_called()

    @pytest.mark.parametrize(
        "case",
        [
            _PushOperationCase(
                name="upsert", push=lambda service, ingress: service.upsert([ingress])
            ),
            _PushOperationCase(
                name="remove", push=lambda service, ingress: service.remove([ingress.key()])
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_failed_node_fails_the_push_after_every_node_finishes(
        self,
        case: _PushOperationCase,
        service: IngressService,
        failing_node: dict[str, MagicMock],
        slow_node_finished: asyncio.Event,
        worker_1_ingress: Ingress,
    ) -> None:
        with pytest.raises(ApiDeliveryWorkerPushFailedError):
            await case.push(service, worker_1_ingress)
        assert slow_node_finished.is_set()

    @pytest.mark.parametrize(
        "case",
        [
            _PushOperationCase(
                name="upsert", push=lambda service, ingress: service.upsert([ingress])
            ),
            _PushOperationCase(
                name="remove", push=lambda service, ingress: service.remove([ingress.key()])
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_every_failed_node_is_reported(
        self,
        case: _PushOperationCase,
        service: IngressService,
        server_error_node: dict[str, MagicMock],
        worker_1_ingress: Ingress,
    ) -> None:
        with pytest.raises(ApiDeliveryWorkerPushFailedError) as exc_info:
            await case.push(service, worker_1_ingress)
        extra_data = exc_info.value.extra_data
        assert extra_data is not None
        reported = [
            _PushFailure(worker_addr=failure["data"]["worker_addr"], error_type=failure["type"])
            for failure in extra_data["failures"]
        ]
        assert reported == [
            _PushFailure(
                worker_addr=WORKER_1_NODE_A,
                error_type=ApiDeliveryWorkerUnreachableError.error_type,
            ),
            _PushFailure(
                worker_addr=WORKER_1_NODE_B,
                error_type=ApiDeliveryWorkerServerError.error_type,
            ),
        ]
