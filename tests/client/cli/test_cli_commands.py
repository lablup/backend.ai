import re
import uuid

import pytest
from aioresponses import aioresponses
from click.testing import CliRunner

from ai.backend.cli.loader import load_entry_points
from ai.backend.cli.types import ExitCode
from ai.backend.client.config import get_config, set_config


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def cli_entrypoint():
    return load_entry_points(allowlist={"ai.backend.client.cli"})


@pytest.mark.parametrize("help_arg", ["-h", "--help"])
def test_print_help(runner, cli_entrypoint, help_arg):
    result = runner.invoke(cli_entrypoint, [help_arg])
    assert result.exit_code == ExitCode.OK
    assert re.match(r"Usage: ([.\w]+) \[OPTIONS\] COMMAND \[ARGS\]", result.output)


def test_print_help_for_unknown_command(runner, cli_entrypoint):
    result = runner.invoke(cli_entrypoint, ["x-non-existent-command"])
    assert result.exit_code == ExitCode.INVALID_USAGE
    assert re.match(r"Usage: ([.\w]+) \[OPTIONS\] COMMAND \[ARGS\]", result.output)


def test_config(runner, cli_entrypoint, monkeypatch, example_keypair, unused_tcp_port_factory):
    api_port = unused_tcp_port_factory()
    api_url = "http://127.0.0.1:{}".format(api_port)
    set_config(None)
    monkeypatch.setenv("BACKEND_ACCESS_KEY", example_keypair[0])
    monkeypatch.setenv("BACKEND_SECRET_KEY", example_keypair[1])
    monkeypatch.setenv("BACKEND_ENDPOINT", api_url)
    config = get_config()
    result = runner.invoke(cli_entrypoint, ["config"])
    assert result.exit_code == ExitCode.OK
    assert str(config.endpoint) in result.output
    assert config.version in result.output
    assert config.access_key in result.output
    assert config.secret_key[:6] in result.output
    assert config.hash_type in result.output


def test_config_unset(runner, cli_entrypoint, monkeypatch):
    monkeypatch.delenv("BACKEND_ACCESS_KEY", raising=False)
    monkeypatch.delenv("BACKEND_SECRET_KEY", raising=False)
    monkeypatch.delenv("BACKEND_ENDPOINT", raising=False)
    # now this works as "anonymous" session config.
    result = runner.invoke(cli_entrypoint, ["config"])
    assert result.exit_code == ExitCode.OK


# def test_compiler_shortcut(mocker):
#     mocker.patch.object(sys, "argv", ["lcc", "-h"])
#     try:
#         main()
#     except SystemExit:
#         pass
#     assert sys.argv == ["lcc", "-h"]
#
#     mocker.patch.object(sys, "argv", ["lpython", "-h"])
#     try:
#         main()
#     except SystemExit:
#         pass
#     assert sys.argv == ["lpython", "-h"]


def test_run_file_or_code_required(
    runner, cli_entrypoint, monkeypatch, example_keypair, unused_tcp_port_factory
):
    api_port = unused_tcp_port_factory()
    api_url = "http://127.0.0.1:{}".format(api_port)
    monkeypatch.setenv("BACKEND_ACCESS_KEY", example_keypair[0])
    monkeypatch.setenv("BACKEND_SECRET_KEY", example_keypair[1])
    monkeypatch.setenv("BACKEND_ENDPOINT", api_url)
    result = runner.invoke(cli_entrypoint, ["run", "python"])
    assert result.exit_code == ExitCode.INVALID_ARGUMENT
    assert "provide the command-line code snippet" in result.output


@pytest.mark.parametrize(
    "test_case",
    [
        {
            "session_id_or_name": uuid.UUID("00000000-0000-0000-0000-000000000000"),
            "new_session_name": "new-name",
            "expected_exit_code": ExitCode.OK,
        },
        {
            "session_id_or_name": "mock-session-name",
            "new_session_name": "new-name",
            "expected_exit_code": ExitCode.OK,
        },
    ],
    ids=["Rename session by uuid", "Rename session by session name"],
)
def test_rename_session(
    test_case, runner, cli_entrypoint, monkeypatch, example_keypair, unused_tcp_port_factory
):
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
            f"{api_url}/session/{session_id_or_name}/rename?name={new_session_name}", status=204
        )

        result = runner.invoke(
            cli_entrypoint, args=["session", "rename", str(session_id_or_name), new_session_name]
        )
        assert result.exit_code == test_case["expected_exit_code"]
