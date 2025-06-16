import asyncio
from typing import Optional

from ai.backend.client.session import AsyncSession
from ai.backend.common.json import load_json


async def verify_session_events(
    client_session: AsyncSession,
    session_name: str,
    timeout: float,
    expected_event: str,
    failure_events: set[str],
    *,
    expected_termination_reason: Optional[str] = None,
) -> None:
    """
    Verify that a specific event occurs within a timeout period during session lifecycle.

    :param client_session: The AsyncSession instance to use for listening to events.
    :param session_name: The name of the session to listen for events.
    :param timeout: The maximum time to wait for the expected event.
    :param expected_event: The event that is expected to occur.
    :param failure_events: A set of events that indicate a failure in the session.
    :param expected_termination_reason: Optional; if provided, checks that the termination reason matches this value.
    """
    collected_events = set()

    async def collect_events() -> None:
        async with client_session.ComputeSession(session_name).listen_events() as evs:
            async for ev in evs:
                collected_events.add(ev.event)
                if ev.event == "session_terminated":
                    if expected_termination_reason is not None:
                        data = load_json(ev.data)
                        assert data["reason"] == "user-requested", (
                            f"Unexpected termination reason: {data['reason']}"
                        )

                if ev.event == expected_event:
                    return

                if ev.event in failure_events:
                    raise RuntimeError(f"Session failed with event: {ev.event}")

    listener = asyncio.create_task(asyncio.wait_for(collect_events(), timeout))
    try:
        await listener
    except asyncio.TimeoutError as e:
        raise asyncio.TimeoutError(
            f"Timeout after {timeout}s; no success event received, Actual events: {collected_events}"
        ) from e
