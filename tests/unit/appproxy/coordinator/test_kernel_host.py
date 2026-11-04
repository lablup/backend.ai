from __future__ import annotations

import inspect
from dataclasses import dataclass
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
from ai.backend.appproxy.coordinator.config import KernelHostConfig
from ai.backend.appproxy.coordinator.errors.circuit import InvalidKernelHostError
from ai.backend.appproxy.coordinator.kernel_host import KernelHostValidator

_SESSION_ID = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
_TOKEN_ID = UUID("4eeb260b-6cc5-4362-baf3-ea978388becd")


@dataclass(frozen=True)
class _KernelHostCase:
    kernel_host: str
    allow_loopback: bool


class TestKernelHostValidator:
    @pytest.fixture
    def validator_of_the_case(self, case: _KernelHostCase) -> KernelHostValidator:
        return KernelHostValidator(KernelHostConfig(allow_loopback=case.allow_loopback))

    @pytest.fixture
    def validator_with_the_default_config(self) -> KernelHostValidator:
        return KernelHostValidator(KernelHostConfig.model_validate({}))

    @pytest.mark.parametrize(
        "case",
        [
            _KernelHostCase(kernel_host="10.0.0.1", allow_loopback=False),
            _KernelHostCase(kernel_host="172.17.0.2", allow_loopback=False),
            _KernelHostCase(kernel_host="192.168.1.100", allow_loopback=False),
            _KernelHostCase(kernel_host="fd00::1", allow_loopback=False),
            _KernelHostCase(kernel_host="agent-1.example.com", allow_loopback=False),
            _KernelHostCase(kernel_host="agent_1", allow_loopback=False),
            _KernelHostCase(kernel_host="127.0.0.1", allow_loopback=True),
            _KernelHostCase(kernel_host="::1", allow_loopback=True),
            _KernelHostCase(kernel_host="::ffff:127.0.0.1", allow_loopback=True),
            _KernelHostCase(kernel_host="localhost", allow_loopback=True),
        ],
        ids=lambda case: f"{case.kernel_host}-allow_loopback={case.allow_loopback}",
    )
    def test_allowed(
        self, case: _KernelHostCase, validator_of_the_case: KernelHostValidator
    ) -> None:
        validator_of_the_case.ensure_allowed(case.kernel_host)

    @pytest.mark.parametrize(
        "case",
        [
            _KernelHostCase(kernel_host="127.0.0.1", allow_loopback=False),
            _KernelHostCase(kernel_host="127.1.2.3", allow_loopback=False),
            _KernelHostCase(kernel_host="::1", allow_loopback=False),
            _KernelHostCase(kernel_host="::ffff:127.0.0.1", allow_loopback=False),
            _KernelHostCase(kernel_host="localhost", allow_loopback=False),
            _KernelHostCase(kernel_host="LOCALHOST", allow_loopback=False),
            _KernelHostCase(kernel_host="localhost.", allow_loopback=False),
            _KernelHostCase(kernel_host="app.localhost", allow_loopback=False),
            _KernelHostCase(kernel_host="169.254.169.254", allow_loopback=True),
            _KernelHostCase(kernel_host="::ffff:169.254.169.254", allow_loopback=True),
            _KernelHostCase(kernel_host="fe80::1", allow_loopback=True),
            _KernelHostCase(kernel_host="224.0.0.1", allow_loopback=True),
            _KernelHostCase(kernel_host="ff02::1", allow_loopback=True),
            _KernelHostCase(kernel_host="0.0.0.0", allow_loopback=True),
            _KernelHostCase(kernel_host="::", allow_loopback=True),
            _KernelHostCase(kernel_host="127.1", allow_loopback=True),
            _KernelHostCase(kernel_host="2130706433", allow_loopback=True),
            _KernelHostCase(kernel_host="0x7f.0.0.1", allow_loopback=True),
            _KernelHostCase(kernel_host="127.0.0.1.", allow_loopback=True),
            _KernelHostCase(kernel_host="", allow_loopback=True),
            _KernelHostCase(kernel_host="host name", allow_loopback=True),
            _KernelHostCase(kernel_host="host/path", allow_loopback=True),
            _KernelHostCase(kernel_host="user@host", allow_loopback=True),
            _KernelHostCase(kernel_host="host:80", allow_loopback=True),
            _KernelHostCase(kernel_host="10.0.0.1\nbackend=10.0.0.2,80", allow_loopback=True),
        ],
        ids=lambda case: f"{case.kernel_host!r}-allow_loopback={case.allow_loopback}",
    )
    def test_rejected(
        self, case: _KernelHostCase, validator_of_the_case: KernelHostValidator
    ) -> None:
        with pytest.raises(InvalidKernelHostError):
            validator_of_the_case.ensure_allowed(case.kernel_host)

    def test_loopback_is_rejected_by_default(
        self, validator_with_the_default_config: KernelHostValidator
    ) -> None:
        with pytest.raises(InvalidKernelHostError):
            validator_with_the_default_config.ensure_allowed("127.0.0.1")


class TestAppSessionEntryPoints:
    @pytest.fixture
    def coordinator_request(self) -> web.Request:
        root_ctx = MagicMock()
        root_ctx.local_config.proxy_coordinator.allow_unauthorized_configure_request = True
        root_ctx.kernel_host_validator = KernelHostValidator(KernelHostConfig(allow_loopback=False))
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
