from typing import Any

import pytest

from ai.backend.kernel.service import ServiceArgumentInterpolator, ServiceParser


class TestModelServiceStringCommand:
    @pytest.fixture
    def service_parser(self) -> ServiceParser:
        return ServiceParser({})

    @pytest.mark.parametrize("shell", [None, ""])
    async def test_without_shell_is_split(
        self,
        service_parser: ServiceParser,
        shell: str | None,
    ) -> None:
        service_parser.add_model_service(
            "model",
            {
                "start_command": "python service.py --flag 'a b'",
                "shell": shell,
                "pre_start_actions": [],
            },
        )

        cmdargs, env = await service_parser.start_service("model", set(), {})

        assert cmdargs == ["python", "service.py", "--flag", "a b"]
        assert env == {}

    async def test_with_shell_uses_shell_c(self, service_parser: ServiceParser) -> None:
        service_parser.add_model_service(
            "model",
            {
                "start_command": "python service.py && echo ok",
                "shell": "/bin/bash",
                "pre_start_actions": [],
            },
        )

        cmdargs, env = await service_parser.start_service("model", set(), {})

        assert cmdargs == ["/bin/bash", "-c", "python service.py && echo ok"]
        assert env == {}


def test_service_argument_interpolation_intrinsic_python_style() -> None:
    command = ["bash", "-c", 'echo "host = {host}, port = {ports[1]}"']
    variables = {
        "host": "99.99.99.99",
        "ports": [11001, 11002],
    }
    ret = ServiceArgumentInterpolator.apply(command, variables)

    assert ret[0] == "bash"  # unchanged
    assert ret[1] == "-c"  # unchanged
    assert ret[2] == 'echo "host = 99.99.99.99, port = 11002"'


def test_service_argument_interpolation_intrinsic_github_style() -> None:
    command = ["bash", "-c", 'echo "host = ${{ host }}, port = ${{ ports[1] }}"']
    variables = {
        "host": "99.99.99.99",
        "ports": [11001, 11002],
    }
    ret = ServiceArgumentInterpolator.apply(command, variables)

    assert ret[0] == "bash"  # unchanged
    assert ret[1] == "-c"  # unchanged
    assert ret[2] == 'echo "host = 99.99.99.99, port = 11002"'


def test_service_argument_interpolation_skip_shell_envvar_simple() -> None:
    command = ["bash", "-c", 'echo "kernel_id = $BACKENDAI_KERNEL_ID"']
    variables: dict[str, Any] = {}
    ret = ServiceArgumentInterpolator.apply(command, variables)

    assert ret[0] == "bash"  # unchanged
    assert ret[1] == "-c"  # unchanged
    assert ret[2] == 'echo "kernel_id = $BACKENDAI_KERNEL_ID"'  # unchanged


def test_service_argument_interpolation_skip_shell_envvar_braced() -> None:
    command = ["bash", "-c", 'echo "kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}"']
    variables: dict[str, Any] = {}
    ret = ServiceArgumentInterpolator.apply(command, variables)

    assert ret[0] == "bash"  # unchanged
    assert ret[1] == "-c"  # unchanged
    assert ret[2] == 'echo "kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}"'  # unchanged


def test_service_argument_interpolation_mixed() -> None:
    command = [
        "bash",
        "-c",
        'echo "host = ${{ host }}, kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}, port = {ports[0]}"',
    ]
    variables = {
        "host": "99.99.99.99",
        "ports": [11001, 11002],
    }
    ret = ServiceArgumentInterpolator.apply(command, variables)

    assert ret[0] == "bash"  # unchanged
    assert ret[1] == "-c"  # unchanged
    assert (
        ret[2]
        == 'echo "host = 99.99.99.99, kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}, port = 11001"'
    )
