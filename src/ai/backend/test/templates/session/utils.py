from typing import Optional

from ai.backend.client.session import AsyncSession
from ai.backend.common.json import load_json


async def verify_session_events(
    client_session: AsyncSession,
    session_name: str,
    expected_event: str,
    failure_events: set[str],
    *,
    expected_termination_reason: Optional[str] = None,
    expected_failure_reason: Optional[str] = None,
) -> None:
    """
    Verify that a specific event occurs during session lifecycle.

    :param client_session: The AsyncSession instance to use for listening to events.
    :param session_name: The name of the session to listen for events.
    :param expected_event: The event that is expected to occur.
    :param failure_events: A set of events that indicate a failure in the session.
    :param expected_termination_reason: Optional; if provided, checks that the termination reason matches this value.
    :param expected_failure_reason: Optional; if provided, checks that the failure reason matches this value.
    """

    async with client_session.ComputeSession(session_name).listen_events() as evs:
        async for ev in evs:
            if ev.event == "session_terminated":
                if expected_termination_reason is not None:
                    data = load_json(ev.data)
                    assert data["reason"] == expected_termination_reason, (
                        f"Unexpected termination reason: {data['reason']}"
                    )

            if ev.event == "session_failure":
                if expected_failure_reason is not None:
                    data = load_json(ev.data)
                    assert data["reason"] == expected_failure_reason, (
                        f"Unexpected failure reason: {data['reason']}"
                    )

            if ev.event == expected_event:
                return

            if ev.event in failure_events:
                raise RuntimeError(
                    f"Session failed with event: {ev.event}, Expected event: {expected_event}"
                )


async def verify_bgtask_events(
    client_session: AsyncSession,
    bgtask_id: str,
    expected_event: str,
    failure_events: set[str],
) -> Optional[str]:
    """
    Verify that a specific background task event occurs.

    :param client_session: The AsyncSession instance to use for listening to events.
    :param bgtask_id: The ID of the background task to listen for events.
    :param expected_event: The event that is expected to occur.
    :param failure_events: A set of events that indicate a failure in the background task.

    :return: The message of the BgTaskEvent
    """

    async with client_session.BackgroundTask(bgtask_id).listen_events() as response:
        async for ev in response:
            if ev.event == expected_event:
                data = load_json(ev.data)
                return data.get("message")

            if ev.event in failure_events:
                raise RuntimeError(
                    f"Got failure event: {ev.event}, Expected event: {expected_event}"
                )
    return None
