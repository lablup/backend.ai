import asyncio
from typing import Awaitable, Callable
from uuid import UUID

from ai.backend.client.func.session import ComputeSession
from ai.backend.client.session import AsyncSession
from ai.backend.common.json import load_json


async def verify_batch_session(
    client_session: AsyncSession,
    session_name: str,
    timeout: float,
    session_factory: Callable[[], Awaitable["ComputeSession"]],
) -> UUID:
    EXPECTED_EVENTS: set[str] = {
        "session_enqueued",
        "session_scheduled",
        "kernel_preparing",
        "kernel_creating",
        "kernel_started",
        "session_started",
        "session_terminating",
        "session_terminated",
        "kernel_terminating",
        "kernel_terminated",
        "session_success",
    }

    collected_events: set[str] = set()

    async def collect_events() -> None:
        async with client_session.ComputeSession(session_name).listen_events() as events:
            async for ev in events:
                collected_events.add(ev.event)
                if ev.event == "session_failure" or ev.event == "session_cancelled":
                    raise RuntimeError(f"BatchSession failed with event: {ev.event}")
                if collected_events == EXPECTED_EVENTS:
                    break

    listener = asyncio.create_task(asyncio.wait_for(collect_events(), timeout))

    created = await session_factory()
    assert created.created, "Session should be created successfully"
    assert created.name == session_name, "Session name mismatch"

    try:
        await listener
        assert created.status in {"TERMINATING", "TERMINATED"}, (
            f"Unexpected final status: {created.status}"
        )
        if created.id is None:
            raise RuntimeError("Session ID is None after creation")
        return created.id
    except asyncio.TimeoutError as e:
        raise asyncio.TimeoutError(
            f"Timed out after {timeout}s; events so far: {collected_events}"
        ) from e


async def verify_interactive_session_creation(
    client_session: AsyncSession,
    session_name: str,
    timeout: float,
    create_session: Callable[[], Awaitable["ComputeSession"]],
) -> UUID:
    EXPECTED_CREATION_EVENTS: set[str] = {
        "session_enqueued",
        "session_scheduled",
        "kernel_preparing",
        "kernel_creating",
        "kernel_started",
        "session_started",
    }

    collected: set[str] = set()

    async def collect_events() -> None:
        async with client_session.ComputeSession(session_name).listen_events() as evs:
            async for ev in evs:
                collected.add(ev.event)
                if ev.event == "session_cancelled":
                    raise RuntimeError("Session creation was cancelled")
                if collected == EXPECTED_CREATION_EVENTS:
                    break

    listener = asyncio.create_task(asyncio.wait_for(collect_events(), timeout))
    created = await create_session()

    assert created.created, "Session creation failed"
    assert created.name == session_name

    try:
        await listener
        assert created.status == "RUNNING", f"Expected RUNNING, got {created.status}"
        if created.id is None:
            raise RuntimeError("Session ID is None after creation")
        return created.id
    except asyncio.TimeoutError as e:
        raise asyncio.TimeoutError(f"Timeout after {timeout}s; events so far: {collected}") from e


async def verify_interactive_session_destruction(
    client_session: AsyncSession,
    session_name: str,
    timeout: float,
) -> None:
    EXPECTED_DESTRUCTION_EVENTS: set[str] = {
        "session_terminating",
        "session_terminated",
        "kernel_terminating",
        "kernel_terminated",
    }
    collected: set[str] = set()

    async def collect_events() -> None:
        async with client_session.ComputeSession(session_name).listen_events() as evs:
            async for ev in evs:
                data = load_json(ev.data)
                assert data["reason"] == "user-requested", (
                    f"Unexpected termination reason: {data['reason']}"
                )
                collected.add(ev.event)
                if ev.event == "session_cancelled":
                    raise RuntimeError("Session creation was cancelled")
                if collected == EXPECTED_DESTRUCTION_EVENTS:
                    break

    listener = asyncio.create_task(asyncio.wait_for(collect_events(), timeout))
    result = await client_session.ComputeSession(session_name).destroy()
    assert result["stats"]["status"] == "terminated", f"Expected terminated, got {result['stats']}"

    try:
        await listener
    except asyncio.TimeoutError as e:
        raise asyncio.TimeoutError(f"Timeout after {timeout}s; events so far: {collected}") from e
