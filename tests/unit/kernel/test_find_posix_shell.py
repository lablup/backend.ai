from pathlib import Path

from ai.backend.kernel import utils
from ai.backend.runner import entrypoint


def _executable(path: Path) -> str:
    path.write_text("#!/bin/true\n")
    path.chmod(0o755)
    return str(path)


def test_candidate_order_matches_the_container_launcher() -> None:
    """The kernel runner must resolve the same shell the launcher started the container with."""
    assert utils.POSIX_SHELL_CANDIDATES == entrypoint.SHELL_CANDIDATES


def test_returns_first_existing_candidate(tmp_path: Path) -> None:
    bash = _executable(tmp_path / "bash")
    assert utils.find_posix_shell([str(tmp_path / "sh"), bash]) == bash


def test_falls_back_to_bin_sh_when_nothing_exists(tmp_path: Path) -> None:
    assert utils.find_posix_shell([str(tmp_path / "sh"), str(tmp_path / "bash")]) == "/bin/sh"
