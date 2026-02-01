from __future__ import annotations

from typing import Optional
from uuid import UUID

from ai.backend.client.request import Request, SSEContextManager

from .base import BaseFunction, api_function

__all__ = ("Events",)


class Events(BaseFunction):
    """
    Provides access to event streaming APIs in Backend.AI.

    This class allows clients to subscribe to real-time events
    such as session lifecycle events and background task events.
    """

    @api_function
    @classmethod
    def listen_session_events(
        cls,
        *,
        session_name: str = "*",
        owner_access_key: Optional[str] = None,
        session_id: Optional[UUID] = None,
        group_name: str = "*",
        scope: str = "*",
    ) -> SSEContextManager:
        """
        Opens a stream of session-related events.

        This method subscribes to real-time events for sessions and their kernels,
        providing updates about their lifecycle and status changes.

        :param session_name: The session name to filter events. Use "*" for all sessions
            (default). If session_id is provided, this parameter is ignored.
        :param owner_access_key: The access key of the session owner. If not provided,
            uses the current API session's access key.
        :param session_id: The specific session ID to monitor. If provided, overrides
            session_name and owner_access_key parameters.
        :param group_name: The group name to filter events. Use "*" for all groups
            (default).
        :param scope: The event scope to subscribe to. Can be "session", "kernel",
            or "session,kernel" (default is "*" which includes both).

        :returns: An SSEContextManager for receiving server-sent events.

        Example usage:
            async with Events.listen_session_events(session_name="my-session") as event_stream:
                async for event in event_stream:
                    print(f"Received event: {event}")
        """
        params: dict[str, str] = {
            "sessionName": session_name,
            "group": group_name,
            "scope": scope,
        }
        if owner_access_key is not None:
            params["ownerAccessKey"] = owner_access_key
        if session_id is not None:
            params["sessionId"] = str(session_id)

        request = Request(
            "GET",
            "/events/session",
            params=params,
        )
        return request.connect_events()

    @api_function
    @classmethod
    def listen_background_task_events(
        cls,
        task_id: UUID,
    ) -> SSEContextManager:
        """
        Opens a stream of background task events.

        This method subscribes to real-time events for a specific background task,
        providing updates about its progress and completion status.

        :param task_id: The UUID of the background task to monitor.

        :returns: An SSEContextManager for receiving server-sent events.

        Example usage:
            task_id = UUID("...")
            async with Events.listen_background_task_events(task_id) as event_stream:
                async for event in event_stream:
                    print(f"Task event: {event}")
                    if event.get("status") == "completed":
                        break
        """
        request = Request(
            "GET",
            "/events/background-task",
            params={
                "taskId": str(task_id),
            },
        )
        return request.connect_events()
