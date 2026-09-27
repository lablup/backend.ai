from __future__ import annotations

import logging
import uuid
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from callosum.rpc import RPCMessage
from callosum.rpc.message import RPCMessageTypes
from pydantic import ValidationError

from ai.backend.agent.errors.agent import ImagePullFailedError, ImagePullTimeoutError
from ai.backend.agent.rpc.context import with_rpc_context
from ai.backend.agent.server import AgentRPCServer, RPCFunctionRegistry
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.message_queue.types import MessageMetadata
from ai.backend.common.types import AgentId
from ai.backend.logging.structured import StructuredLogger

SERVER_LOGGER = "ai.backend.agent.server"
TEST_LOGGER = "tests.agent.rpc_log_context"
PRIMARY_AGENT_ID = AgentId("i-primary")
TRACE_LEVEL = 5


def _user() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


def _request(
    method: str,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
    metadata: MessageMetadata | None = None,
) -> RPCMessage:
    body: dict[str, Any] = {"args": args, "kwargs": kwargs or {}}
    if metadata is not None:
        body["metadata"] = metadata.model_dump(mode="json")
    return RPCMessage(None, RPCMessageTypes.FUNCTION, method, "", 0, None, body)


def _raw_request(method: str, body: dict[str, Any]) -> RPCMessage:
    return RPCMessage(None, RPCMessageTypes.FUNCTION, method, "", 0, None, body)


def _server(agent: MagicMock | None = None) -> AgentRPCServer:
    if agent is None:
        agent = MagicMock()
        agent.id = PRIMARY_AGENT_ID
    agent.produce_error_event = AsyncMock()
    server = MagicMock()
    server.runtime.get_agent.return_value = agent
    server.error_monitor.capture_exception = AsyncMock()
    return cast(AgentRPCServer, server)


@pytest.fixture
def capture(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    with (
        caplog.at_level(TRACE_LEVEL, logger=SERVER_LOGGER),
        caplog.at_level(TRACE_LEVEL, logger=TEST_LOGGER),
    ):
        yield caplog


class TestWithRPCContext:
    def test_restores_metadata_and_scopes_logs(self, capture: pytest.LogCaptureFixture) -> None:
        user = _user()
        request_id = str(uuid.uuid4())
        request = _request(
            "destroy_kernel",
            metadata=MessageMetadata(request_id=request_id, user=user, triggered_user=user),
        )
        log = StructuredLogger(logging.getLogger(TEST_LOGGER))

        with with_rpc_context(request, PRIMARY_AGENT_ID):
            assert current_request_id() == request_id
            assert current_user() == user
            log.info("inside")

        record = capture.records[0]
        assert record.__dict__["log_tag_request_id"] == request_id
        assert record.__dict__["log_tag_user_id"] == str(user.user_id)
        assert record.__dict__["log_tag_rpc_method"] == "destroy_kernel"
        assert record.__dict__["log_tag_agent_id"] == PRIMARY_AGENT_ID
        assert current_request_id() is None

    def test_request_without_metadata_is_not_restored(
        self, capture: pytest.LogCaptureFixture
    ) -> None:
        request = _request("ping")
        log = StructuredLogger(logging.getLogger(TEST_LOGGER))

        with with_rpc_context(request, PRIMARY_AGENT_ID):
            assert current_request_id() is None
            assert current_user() is None
            log.info("inside")

        record = capture.records[0]
        assert "log_tag_request_id" not in record.__dict__
        assert record.__dict__["log_tag_rpc_method"] == "ping"


class TestRPCFunctionRegistry:
    async def test_failure_is_logged_with_rpc_and_kernel_scope(
        self, capture: pytest.LogCaptureFixture
    ) -> None:
        registry = RPCFunctionRegistry()

        async def restart_kernel(
            self: AgentRPCServer, session_id: str, kernel_id: str, agent_id: str | None = None
        ) -> None:
            raise RuntimeError("boom")

        handler = registry(restart_kernel)
        with pytest.raises(RuntimeError):
            await handler(_server(), _request("restart_kernel", ("s-1", "k-1")))

        errors = [r for r in capture.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert errors[0].__dict__["log_tag_rpc_method"] == "restart_kernel"
        assert errors[0].__dict__["log_tag_agent_id"] == PRIMARY_AGENT_ID
        assert errors[0].__dict__["log_tag_session_id"] == "s-1"
        assert errors[0].__dict__["log_tag_kernel_id"] == "k-1"
        assert errors[0].exc_info is not None

    async def test_handler_logging_own_failure_is_not_logged_again(
        self, capture: pytest.LogCaptureFixture
    ) -> None:
        registry = RPCFunctionRegistry()

        async def create_kernels(self: AgentRPCServer) -> None:
            raise RuntimeError("boom")

        handler = registry.logs_own_failure(create_kernels)
        server = _server()
        with pytest.raises(RuntimeError):
            await handler(server, _request("create_kernels"))

        assert [r for r in capture.records if r.levelno == logging.ERROR] == []
        cast(AsyncMock, server.error_monitor.capture_exception).assert_awaited_once()

    async def test_handler_sees_restored_request_id(self) -> None:
        registry = RPCFunctionRegistry()
        request_id = str(uuid.uuid4())
        seen: list[str | None] = []

        async def ping(self: AgentRPCServer, msg: str) -> str:
            seen.append(current_request_id())
            return msg

        handler = registry(ping)
        result = await handler(
            _server(),
            _request("ping", ("hi",), metadata=MessageMetadata(request_id=request_id)),
        )

        assert result == "hi"
        assert seen == [request_id]

    @pytest.mark.parametrize("logs_own_failure", [False, True])
    async def test_failure_before_scope_is_logged_once(
        self, capture: pytest.LogCaptureFixture, logs_own_failure: bool
    ) -> None:
        registry = RPCFunctionRegistry()

        async def ping(self: AgentRPCServer, msg: str) -> str:
            return msg

        handler = registry.logs_own_failure(ping) if logs_own_failure else registry(ping)
        server = _server()
        invalid_metadata = {"args": ("hi",), "kwargs": {}, "metadata": {"user": "invalid"}}
        with pytest.raises(ValidationError):
            await handler(server, _raw_request("ping", invalid_metadata))

        errors = [r for r in capture.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert "log_tag_rpc_method" not in errors[0].__dict__
        assert errors[0].exc_info is not None
        cast(AsyncMock, server.error_monitor.capture_exception).assert_awaited_once()


class TestCreateKernels:
    async def test_kernel_failure_is_logged_once_in_kernel_scope(
        self, capture: pytest.LogCaptureFixture
    ) -> None:
        session_id = uuid.uuid4()
        kernel_id = uuid.uuid4()
        agent = MagicMock()
        agent.id = PRIMARY_AGENT_ID
        agent.local_config.agent.kernel_creation_concurrency = 1
        agent.create_kernel = AsyncMock(side_effect=RuntimeError("docker failure"))
        image_ref = MagicMock()
        image_ref.canonical = "cr.backend.ai/stable/python:latest"

        with pytest.raises(RuntimeError):
            await AgentRPCServer.create_kernels(
                _server(agent),
                _request(
                    "create_kernels",
                    (str(session_id), [str(kernel_id)], [{}], {}, {kernel_id: image_ref}),
                ),
            )

        errors = [r for r in capture.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert errors[0].__dict__["log_tag_rpc_method"] == "create_kernels"
        assert errors[0].__dict__["log_tag_session_id"] == str(session_id)
        assert errors[0].__dict__["log_tag_kernel_id"] == str(kernel_id)
        assert errors[0].exc_info is not None

    async def test_failure_outside_kernels_is_logged_once(
        self, capture: pytest.LogCaptureFixture
    ) -> None:
        agent = MagicMock()
        agent.id = PRIMARY_AGENT_ID
        agent.local_config.agent.kernel_creation_concurrency = 1

        with pytest.raises(KeyError):
            await AgentRPCServer.create_kernels(
                _server(agent),
                _request(
                    "create_kernels",
                    (str(uuid.uuid4()), [str(uuid.uuid4())], [{}], {}, {}),
                ),
            )

        errors = [r for r in capture.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert errors[0].__dict__["log_tag_rpc_method"] == "create_kernels"
        assert "log_tag_kernel_id" not in errors[0].__dict__
        assert errors[0].exc_info is not None

    @pytest.mark.parametrize(
        "pull_error",
        [ImagePullFailedError("pull failed"), ImagePullTimeoutError("pull timed out")],
    )
    async def test_image_pull_failure_is_not_logged_at_info_or_above(
        self, capture: pytest.LogCaptureFixture, pull_error: Exception
    ) -> None:
        kernel_id = uuid.uuid4()
        agent = MagicMock()
        agent.id = PRIMARY_AGENT_ID
        agent.local_config.agent.kernel_creation_concurrency = 1
        agent.create_kernel = AsyncMock(side_effect=pull_error)
        image_ref = MagicMock()
        image_ref.canonical = "cr.backend.ai/stable/python:latest"

        with pytest.raises(type(pull_error)):
            await AgentRPCServer.create_kernels(
                _server(agent),
                _request(
                    "create_kernels",
                    (str(uuid.uuid4()), [str(kernel_id)], [{}], {}, {kernel_id: image_ref}),
                ),
            )

        assert [r for r in capture.records if r.levelno >= logging.INFO] == []
        assert [r.getMessage() for r in capture.records if r.levelno == TRACE_LEVEL] == [
            "kernel image pull failed"
        ]
