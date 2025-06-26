from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CreatedSessionMetaContext
from ai.backend.test.templates.template import TestCode


class SessionStatusHistoryRetriever(TestCode):
    @override
    async def test(self) -> None:
        session = ClientSessionContext.current()
        session_meta = CreatedSessionMetaContext.current()
        session_name = session_meta.name

        expected_status = set([
            "SCHEDULED",
            "PREPARING",
            "PULLING",
            "PREPARED",
            "PENDING",
            "CREATING",
            "RUNNING",
        ])

        unexpected_status = set([
            "TERMINATING",
            "TERMINATED",
            "EXPIRED",
        ])

        result = await session.ComputeSession(name=session_name).get_status_history()
        assert result["result"] != "", "Status history should not be empty"
        for status_key, _status_value in result["result"].items():
            assert status_key in expected_status, (
                f"Status {status_key} is not a valid session status"
            )
            assert status_key not in unexpected_status, (
                f"Status {status_key} should not be in the history"
            )
