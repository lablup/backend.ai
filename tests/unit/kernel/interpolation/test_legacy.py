from typing import Any

from ai.backend.kernel.interpolation.legacy import LegacyInterpolator


class TestLegacyInterpolator:
    def test_intrinsic_python_style(self) -> None:
        command = ["bash", "-c", 'echo "host = {host}, port = {ports[1]}"']
        variables = {
            "host": "99.99.99.99",
            "ports": [11001, 11002],
        }
        ret = LegacyInterpolator(variables).apply(command)

        assert ret[0] == "bash"  # unchanged
        assert ret[1] == "-c"  # unchanged
        assert ret[2] == 'echo "host = 99.99.99.99, port = 11002"'

    def test_intrinsic_github_style(self) -> None:
        command = ["bash", "-c", 'echo "host = ${{ host }}, port = ${{ ports[1] }}"']
        variables = {
            "host": "99.99.99.99",
            "ports": [11001, 11002],
        }
        ret = LegacyInterpolator(variables).apply(command)

        assert ret[0] == "bash"  # unchanged
        assert ret[1] == "-c"  # unchanged
        assert ret[2] == 'echo "host = 99.99.99.99, port = 11002"'

    def test_skip_shell_envvar_simple(self) -> None:
        command = ["bash", "-c", 'echo "kernel_id = $BACKENDAI_KERNEL_ID"']
        variables: dict[str, Any] = {}
        ret = LegacyInterpolator(variables).apply(command)

        assert ret[0] == "bash"  # unchanged
        assert ret[1] == "-c"  # unchanged
        assert ret[2] == 'echo "kernel_id = $BACKENDAI_KERNEL_ID"'  # unchanged

    def test_skip_shell_envvar_braced(self) -> None:
        command = ["bash", "-c", 'echo "kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}"']
        variables: dict[str, Any] = {}
        ret = LegacyInterpolator(variables).apply(command)

        assert ret[0] == "bash"  # unchanged
        assert ret[1] == "-c"  # unchanged
        assert ret[2] == 'echo "kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}"'  # unchanged

    def test_mixed(self) -> None:
        command = [
            "bash",
            "-c",
            'echo "host = ${{ host }}, kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}, port = {ports[0]}"',
        ]
        variables = {
            "host": "99.99.99.99",
            "ports": [11001, 11002],
        }
        ret = LegacyInterpolator(variables).apply(command)

        assert ret[0] == "bash"  # unchanged
        assert ret[1] == "-c"  # unchanged
        assert (
            ret[2]
            == 'echo "host = 99.99.99.99, kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}, port = 11001"'
        )
