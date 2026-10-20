from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from ai.backend.appproxy.common.config import SecretConfig
from ai.backend.appproxy.coordinator.errors.ingress import (
    ApiDeliveryWorkerRejectedError,
    ApiDeliveryWorkerServerError,
    ApiDeliveryWorkerUnreachableError,
)
from ai.backend.appproxy.coordinator.ingress.client import (
    ApiDeliveryWorkerClient,
    ApiDeliveryWorkerClientPool,
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
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)
from ai.backend.common.exception import BackendAIError

API_SECRET = "api-secret"
WORKER_ADDR = "10.0.0.1:10201"


@dataclass(frozen=True)
class _ErrorAnswerCase:
    status: HTTPStatus
    expected_error: type[BackendAIError]


def _answering_session(status: int, body: bytes) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.read = AsyncMock(return_value=body)
    session = MagicMock()
    session.post.return_value.__aenter__.return_value = response
    return session


@pytest.fixture
def secrets() -> SecretConfig:
    return SecretConfig(api_secret=API_SECRET, jwt_secret="jwt-secret")


@pytest.fixture
def ingress() -> Ingress:
    return Ingress(
        id=IngressID("ingress-1"),
        authority=IngressAuthority("worker-1"),
        revision=3,
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
def applying_session() -> MagicMock:
    return _answering_session(HTTPStatus.OK, b"")


@pytest.fixture
def unreachable_session() -> MagicMock:
    session = MagicMock()
    session.post.side_effect = aiohttp.ClientConnectionError("connection refused")
    return session


class TestApiDeliveryWorkerClient:
    async def test_push_carries_the_api_secret(
        self, applying_session: MagicMock, secrets: SecretConfig, ingress: Ingress
    ) -> None:
        client = ApiDeliveryWorkerClient(applying_session, WORKER_ADDR, secrets)
        await client.upsert([ingress])
        assert applying_session.post.call_args.kwargs["headers"] == {
            "X-BackendAI-Token": API_SECRET
        }

    @pytest.mark.parametrize(
        "case",
        [
            _ErrorAnswerCase(
                status=HTTPStatus.BAD_REQUEST, expected_error=ApiDeliveryWorkerRejectedError
            ),
            _ErrorAnswerCase(
                status=HTTPStatus.UNAUTHORIZED, expected_error=ApiDeliveryWorkerRejectedError
            ),
            _ErrorAnswerCase(
                status=HTTPStatus.CONFLICT, expected_error=ApiDeliveryWorkerRejectedError
            ),
            _ErrorAnswerCase(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                expected_error=ApiDeliveryWorkerServerError,
            ),
            _ErrorAnswerCase(
                status=HTTPStatus.NOT_IMPLEMENTED, expected_error=ApiDeliveryWorkerServerError
            ),
        ],
        ids=lambda case: str(case.status.value),
    )
    async def test_error_answer_raises_with_the_worker_status(
        self, case: _ErrorAnswerCase, secrets: SecretConfig, ingress: Ingress
    ) -> None:
        session = _answering_session(case.status, b"rejected")
        client = ApiDeliveryWorkerClient(session, WORKER_ADDR, secrets)
        with pytest.raises(case.expected_error) as exc_info:
            await client.upsert([ingress])
        assert exc_info.value.extra_data == {
            "worker_addr": WORKER_ADDR,
            "status": case.status,
            "body": "rejected",
        }

    async def test_unreachable_worker_raises(
        self, unreachable_session: MagicMock, secrets: SecretConfig, ingress: Ingress
    ) -> None:
        client = ApiDeliveryWorkerClient(unreachable_session, WORKER_ADDR, secrets)
        with pytest.raises(ApiDeliveryWorkerUnreachableError):
            await client.upsert([ingress])


class TestApiDeliveryWorkerClientPool:
    async def test_client_of_an_address_is_reused(self, secrets: SecretConfig) -> None:
        pool = ApiDeliveryWorkerClientPool(secrets)
        try:
            assert pool.load_client(WORKER_ADDR) is pool.load_client(WORKER_ADDR)
        finally:
            await pool.close()
