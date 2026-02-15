from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import aiohttp
import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.event_stream import EventStreamClient
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.client.v2.streaming_types import SSEConnection
from ai.backend.common.dto.manager.event_stream import (
    BgtaskDonePayload,
    BgtaskUpdatedPayload,
    SessionEventPayload,
    SessionKernelEventPayload,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


def _make_event_stream_client(mock_session: MagicMock) -> EventStreamClient:
    return EventStreamClient(_make_client(mock_session))


def _make_sse_response(lines: list[bytes]) -> AsyncMock:
    line_iter = iter(lines)

    async def _readline() -> bytes:
        try:
            return next(line_iter)
        except StopIteration:
            return b""

    mock_resp = AsyncMock(spec=aiohttp.ClientResponse)
    mock_resp.status = 200
    mock_resp.reason = "OK"
    mock_resp.content = MagicMock()
    mock_resp.content.readline = _readline
    mock_resp.close = MagicMock()
    return mock_resp


# ===========================================================================
# SSE — Session events
# ===========================================================================


class TestSubscribeSessionEvents:
    @pytest.mark.asyncio
    async def test_opens_sse_with_default_params(self) -> None:
        mock_resp = _make_sse_response([
            b"event: session_started\n",
            b"data: {}\n",
            b"\n",
            b"",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_event_stream_client(mock_session)

        async with client.subscribe_session_events() as sse:
            assert isinstance(sse, SSEConnection)
            events = []
            async for event in sse:
                events.append(event)

        assert len(events) == 1
        assert events[0].event == "session_started"

        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["params"]["name"] == "*"
        assert call_kwargs["params"]["group"] == "*"
        assert call_kwargs["params"]["scope"] == "*"

    @pytest.mark.asyncio
    async def test_passes_custom_params(self) -> None:
        mock_resp = _make_sse_response([b""])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_event_stream_client(mock_session)

        session_id = UUID("12345678-1234-5678-1234-567812345678")
        async with client.subscribe_session_events(
            session_name="my-sess",
            owner_access_key="AKTEST",
            session_id=session_id,
            group_name="research",
            scope="session,kernel",
        ) as sse:
            async for _ in sse:
                pass

        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["params"]["name"] == "my-sess"
        assert call_kwargs["params"]["ownerAccessKey"] == "AKTEST"
        assert call_kwargs["params"]["sessionId"] == str(session_id)
        assert call_kwargs["params"]["group"] == "research"
        assert call_kwargs["params"]["scope"] == "session,kernel"

    @pytest.mark.asyncio
    async def test_iterates_multiple_events(self) -> None:
        mock_resp = _make_sse_response([
            b"event: session_enqueued\n",
            b'data: {"session_id": "abc"}\n',
            b"\n",
            b"event: session_started\n",
            b'data: {"session_id": "abc"}\n',
            b"\n",
            b"",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_event_stream_client(mock_session)

        events = []
        async with client.subscribe_session_events() as sse:
            async for event in sse:
                events.append(event)

        assert len(events) == 2
        assert events[0].event == "session_enqueued"
        assert events[1].event == "session_started"

    @pytest.mark.asyncio
    async def test_omits_optional_params_when_none(self) -> None:
        mock_resp = _make_sse_response([b""])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_event_stream_client(mock_session)

        async with client.subscribe_session_events() as sse:
            async for _ in sse:
                pass

        call_kwargs = mock_session.get.call_args.kwargs
        assert "ownerAccessKey" not in call_kwargs["params"]
        assert "sessionId" not in call_kwargs["params"]


# ===========================================================================
# SSE — Background task events
# ===========================================================================


class TestSubscribeBackgroundTaskEvents:
    @pytest.mark.asyncio
    async def test_opens_sse_with_task_id(self) -> None:
        mock_resp = _make_sse_response([
            b"event: bgtask_updated\n",
            b'data: {"task_id": "t1", "current_progress": 50}\n',
            b"\n",
            b"",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_event_stream_client(mock_session)

        task_id = UUID("abcdef01-2345-6789-abcd-ef0123456789")
        async with client.subscribe_background_task_events(task_id) as sse:
            assert isinstance(sse, SSEConnection)
            events = []
            async for event in sse:
                events.append(event)

        assert len(events) == 1
        assert events[0].event == "bgtask_updated"

        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["params"]["taskId"] == str(task_id)

    @pytest.mark.asyncio
    async def test_stops_on_server_close(self) -> None:
        mock_resp = _make_sse_response([
            b"event: bgtask_done\n",
            b'data: {"task_id": "t1"}\n',
            b"\n",
            b"event: server_close\n",
            b"data: \n",
            b"\n",
            b"event: should_not_appear\n",
            b"data: ignored\n",
            b"\n",
            b"",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_event_stream_client(mock_session)

        task_id = UUID("abcdef01-2345-6789-abcd-ef0123456789")
        events = []
        async with client.subscribe_background_task_events(task_id) as sse:
            async for event in sse:
                events.append(event)

        assert len(events) == 2
        assert events[0].event == "bgtask_done"
        assert events[1].event == "server_close"


# ===========================================================================
# DTO — Session event payloads
# ===========================================================================


class TestSessionEventPayloads:
    def test_session_event_payload_from_dict(self) -> None:
        data = {
            "reason": "",
            "sessionName": "my-session",
            "ownerAccessKey": "AKTEST",
            "sessionId": "550e8400-e29b-41d4-a716-446655440000",
            "exitCode": None,
        }
        payload = SessionEventPayload.model_validate(data)
        assert payload.session_name == "my-session"
        assert payload.owner_access_key == "AKTEST"
        assert payload.session_id == "550e8400-e29b-41d4-a716-446655440000"
        assert payload.exit_code is None

    def test_session_kernel_event_payload_from_dict(self) -> None:
        data = {
            "reason": "",
            "sessionName": "my-session",
            "ownerAccessKey": "AKTEST",
            "sessionId": "550e8400-e29b-41d4-a716-446655440000",
            "exitCode": 0,
            "kernelId": "kernel-001",
            "clusterRole": "main",
            "clusterIdx": 0,
        }
        payload = SessionKernelEventPayload.model_validate(data)
        assert payload.kernel_id == "kernel-001"
        assert payload.cluster_role == "main"
        assert payload.cluster_idx == 0
        assert payload.exit_code == 0

    def test_session_event_payload_defaults(self) -> None:
        payload = SessionEventPayload.model_validate({})
        assert payload.reason == ""
        assert payload.session_name == ""
        assert payload.owner_access_key == ""
        assert payload.session_id == ""
        assert payload.exit_code is None

    def test_bgtask_payloads_from_dto(self) -> None:
        updated = BgtaskUpdatedPayload.model_validate({
            "task_id": "t1",
            "message": "Processing...",
            "current_progress": 0.5,
            "total_progress": 1.0,
        })
        assert updated.task_id == "t1"
        assert updated.current_progress == 0.5

        done = BgtaskDonePayload.model_validate({
            "task_id": "t1",
            "message": "Completed",
        })
        assert done.message == "Completed"


# ===========================================================================
# Registry — event_stream property
# ===========================================================================


class TestRegistryEventStream:
    def test_registry_has_event_stream_property(self) -> None:
        mock_session = MagicMock()
        backend_client = _make_client(mock_session)
        registry = BackendAIClientRegistry(backend_client)

        es = registry.event_stream
        assert isinstance(es, EventStreamClient)
        # cached_property should return the same instance
        assert registry.event_stream is es
