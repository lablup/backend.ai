from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CodeExecutionContext, CreatedSessionIDContext
from ai.backend.test.templates.template import TestCode


class InteractiveSessionExecuteCodeSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        session_id = CreatedSessionIDContext.current()
        code_dep = CodeExecutionContext.current()

        result = await client_session.ComputeSession(str(session_id)).execute(
            code=code_dep.code,
        )

        assert result["status"] == "finished", (
            f"Expected status to be finished, Actual status: {result['status']}"
        )
        assert result["exitCode"] == 0, (
            f"Expected exitCode to be 0, Actual exitCode: {result['exitCode']}"
        )
        assert result["console"] == [["stdout", code_dep.expected_result]], (
            f"Expected console output to match, Actual value: {result['console']}"
        )

        async with client_session.ComputeSession(str(session_id)).stream_execute(
            code=code_dep.code
        ) as ws:
            result = await ws.receive_json()
            assert result["status"] == "finished", (
                f"Expected status to be finished, Actual status: {result['status']}"
            )
            assert result["exitCode"] == 0, (
                f"Expected exitCode to be 0, Actual exitCode: {result['exitCode']}"
            )
            assert result["console"] == [["stdout", code_dep.expected_result]], (
                f"Expected console output to match, Actual value: {result['console']}"
            )


class InteractiveSessionExecuteCodeFailureWrongCommand(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        session_id = CreatedSessionIDContext.current()
        WRONG_CMD = "some wrong command !@#"

        result = await client_session.ComputeSession(str(session_id)).execute(
            code=WRONG_CMD,
        )

        assert result["status"] == "finished", (
            f"Expected status to be finished, Actual status: {result['status']}"
        )
        # TODO: Is 0 correct exitcode when the command fails?
        assert result["exitCode"] == 0, (
            f"Expected exitCode to be 0, Actual exitCode: {result['exitCode']}"
        )
        assert result["console"][0][0] == "stderr", (
            f"Expected stderr, Actual value: {result['console']}"
        )

        async with client_session.ComputeSession(str(session_id)).stream_execute(
            code=WRONG_CMD
        ) as ws:
            result = await ws.receive_json()
            assert result["status"] == "finished", (
                f"Expected status to be finished, Actual status: {result['status']}"
            )
            assert result["exitCode"] == 0, (
                f"Expected exitCode to be 0, Actual exitCode: {result['exitCode']}"
            )
            assert result["console"][0][0] == "stderr", (
                f"Expected stderr, Actual value: {result['console']}"
            )
