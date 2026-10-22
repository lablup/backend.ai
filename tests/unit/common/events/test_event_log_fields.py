import uuid

from ai.backend.common.events.event_types.agent.anycast import AgentStartedEvent
from ai.backend.common.events.event_types.kernel.anycast import (
    DoSyncKernelLogsEvent,
    KernelPreparingAnycastEvent,
    KernelTerminatedAnycastEvent,
)
from ai.backend.common.events.event_types.session.anycast import SessionStartedAnycastEvent
from ai.backend.common.types import AgentId, KernelId, SessionId

_SOURCE = AgentId("i-agent")


class TestEventLogFields:
    def test_kernel_event_without_session_carries_kernel_id(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        event = DoSyncKernelLogsEvent(kernel_id=kernel_id, container_id="c-1")

        assert event.log_fields(_SOURCE) == {"kernel_id": kernel_id}

    def test_kernel_creation_event_carries_session_id(self) -> None:
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        event = KernelPreparingAnycastEvent(kernel_id=kernel_id, session_id=session_id)

        assert event.log_fields(_SOURCE) == {"kernel_id": kernel_id, "session_id": session_id}

    def test_kernel_termination_event_carries_session_id(self) -> None:
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        event = KernelTerminatedAnycastEvent(kernel_id=kernel_id, session_id=session_id)

        assert event.log_fields(_SOURCE) == {"kernel_id": kernel_id, "session_id": session_id}

    def test_session_event_carries_session_id(self) -> None:
        session_id = SessionId(uuid.uuid4())
        event = SessionStartedAnycastEvent(session_id=session_id, creation_id="c-1")

        assert event.log_fields(_SOURCE) == {"session_id": session_id}

    def test_agent_event_takes_agent_id_from_the_source(self) -> None:
        event = AgentStartedEvent(reason="started")

        assert event.log_fields(_SOURCE) == {"agent_id": _SOURCE}
