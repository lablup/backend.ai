from http import HTTPStatus

import pytest
from aioresponses import aioresponses

from ai.backend.cli.types import ExitCode
from ai.backend.client.config import set_config


@pytest.mark.parametrize(
    "test_case",
    [
        {
            "session_id_or_name": "00000000-0000-0000-0000-000000000000",
            "new_session_name": "new-name",
            "expected_exit_code": ExitCode.OK,
        },
        {
            "session_id_or_name": "mock-session-name",
            "new_session_name": "new-name",
            "expected_exit_code": ExitCode.OK,
        },
    ],
    ids=["Use session command by uuid", "Use session command by session name"],
)
def test_session_command(
    test_case, runner, cli_entrypoint, monkeypatch, example_keypair, unused_tcp_port_factory
):
    """
    Test whether the Session CLI commands work correctly when either session_id or session_name is provided as argument.
    """

    api_port = unused_tcp_port_factory()
    api_url = "http://127.0.0.1:{}".format(api_port)

    set_config(None)
    monkeypatch.setenv("BACKEND_ACCESS_KEY", example_keypair[0])
    monkeypatch.setenv("BACKEND_SECRET_KEY", example_keypair[1])
    monkeypatch.setenv("BACKEND_ENDPOINT", api_url)
    monkeypatch.setenv("BACKEND_ENDPOINT_TYPE", "api")

    with aioresponses() as mocked:
        session_id_or_name = test_case["session_id_or_name"]
        new_session_name = test_case["new_session_name"]

        mocked.post(
            f"{api_url}/session/{session_id_or_name}/rename?name={new_session_name}",
            status=HTTPStatus.NO_CONTENT,
        )

        result = runner.invoke(
            cli_entrypoint, args=["session", "rename", session_id_or_name, new_session_name]
        )
        assert result.exit_code == test_case["expected_exit_code"]
