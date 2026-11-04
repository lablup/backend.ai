from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
import pytest_mock
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.types import ProxyProtocol
from ai.backend.appproxy.coordinator.api.conf import conf_v2
from ai.backend.appproxy.coordinator.api.proxy import ProxyRequestModel, proxy
from ai.backend.appproxy.coordinator.api.types import ConfRequestModel
from ai.backend.appproxy.coordinator.errors.circuit import InvalidKernelHostError
from ai.backend.appproxy.coordinator.kernel_host import ensure_kernel_host_allowed

_SESSION_ID = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
_TOKEN_ID = UUID("4eeb260b-6cc5-4362-baf3-ea978388becd")


class TestEnsureKernelHostAllowed:
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
    def test_allows_the_kernel_host(self, kernel_host: str) -> None:
        ensure_kernel_host_allowed(kernel_host)

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
        with pytest.raises(InvalidKernelHostError):
            ensure_kernel_host_allowed(kernel_host)


class TestAppSessionEntryPoints:
    @pytest.fixture
    def coordinator_request(self) -> web.Request:
        root_ctx = MagicMock()
        root_ctx.local_config.proxy_coordinator.allow_unauthorized_configure_request = True
        app = web.Application()
        app["_root.context"] = root_ctx
        return make_mocked_request("GET", "/", app=app)

    @pytest.fixture
    def token_stored_with_a_metadata_address(self, mocker: pytest_mock.MockerFixture) -> None:
        mocker.patch(
            "ai.backend.appproxy.coordinator.api.proxy.Token.get",
            AsyncMock(
                return_value=MagicMock(kernel_host="169.254.169.254", session_id=_SESSION_ID)
            ),
        )

    @pytest.fixture
    def conf_params_with_a_metadata_address(self) -> ConfRequestModel:
        return ConfRequestModel.model_validate({
            "login_session_token": None,
            "kernel_host": "169.254.169.254",
            "kernel_port": 80,
            "session": {
                "id": str(_SESSION_ID),
                "user_uuid": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
                "group_id": "2de2b969-1d04-48a6-af16-0bc8adb3c831",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "domain_name": "default",
            },
        })

    @pytest.fixture
    def proxy_params_of_a_new_circuit(self) -> ProxyRequestModel:
        return ProxyRequestModel.model_validate({
            "app": "jupyter",
            "protocol": ProxyProtocol.HTTP,
            "token": str(_TOKEN_ID),
            "session_id": _SESSION_ID,
            "no_reuse": True,
        })

    async def test_conf_rejects_the_kernel_host_before_storing_a_token(
        self,
        coordinator_request: web.Request,
        conf_params_with_a_metadata_address: ConfRequestModel,
    ) -> None:
        with pytest.raises(InvalidKernelHostError):
            await inspect.unwrap(conf_v2)(coordinator_request, conf_params_with_a_metadata_address)

        root_ctx = coordinator_request.app["_root.context"]
        root_ctx.db.begin_session.assert_not_called()

    @pytest.mark.usefixtures("token_stored_with_a_metadata_address")
    async def test_proxy_rejects_the_kernel_host_of_a_stored_token(
        self,
        coordinator_request: web.Request,
        proxy_params_of_a_new_circuit: ProxyRequestModel,
    ) -> None:
        with pytest.raises(InvalidKernelHostError):
            await inspect.unwrap(proxy)(coordinator_request, proxy_params_of_a_new_circuit)
