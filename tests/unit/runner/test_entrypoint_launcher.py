import os
from pathlib import Path

import pytest

from ai.backend.runner import entrypoint


def _make_executable(path: Path) -> Path:
    path.write_text("#!/bin/true\n")
    path.chmod(0o755)
    return path


def test_prefers_bin_sh_when_present(tmp_path: Path) -> None:
    sh = _make_executable(tmp_path / "sh")
    bash = _make_executable(tmp_path / "bash")
    assert entrypoint.find_shell([str(sh), str(bash)]) == str(sh)


def test_falls_back_to_next_candidate(tmp_path: Path) -> None:
    bash = _make_executable(tmp_path / "bash")
    assert entrypoint.find_shell([str(tmp_path / "sh"), str(bash)]) == str(bash)


def test_follows_symlinks(tmp_path: Path) -> None:
    dash = _make_executable(tmp_path / "dash")
    sh = tmp_path / "sh"
    sh.symlink_to(dash)
    assert entrypoint.find_shell([str(sh)]) == str(sh)


def test_skips_non_executable_and_directories(tmp_path: Path) -> None:
    plain = tmp_path / "sh"
    plain.write_text("")
    directory = tmp_path / "bash"
    directory.mkdir()
    ash = _make_executable(tmp_path / "ash")
    assert entrypoint.find_shell([str(plain), str(directory), str(ash)]) == str(ash)


def test_returns_none_without_any_shell(tmp_path: Path) -> None:
    assert entrypoint.find_shell([str(tmp_path / "sh")]) is None


def test_main_reports_missing_shell(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(entrypoint, "find_shell", lambda candidates=(): None)
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main(["python", "-m", "ai.backend.kernel"])
    assert exc_info.value.code == 127
    assert "no POSIX shell" in capsys.readouterr().err


class _Exec(Exception):
    pass


def test_main_reports_exec_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing_execv(path: str, args: list[str]) -> None:
        raise OSError(8, "Exec format error")

    monkeypatch.setattr(entrypoint, "find_shell", lambda candidates=(): "/bin/bash")
    monkeypatch.setattr(os, "execv", failing_execv)
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main(["python"])
    assert exc_info.value.code == 126
    assert "Exec format error" in capsys.readouterr().err


def test_main_execs_shell_with_script_and_args(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_execv(path: str, args: list[str]) -> None:
        calls.append((path, args))
        raise _Exec

    monkeypatch.setattr(entrypoint, "find_shell", lambda candidates=(): "/bin/bash")
    monkeypatch.setattr(os, "execv", fake_execv)
    with pytest.raises(_Exec):
        entrypoint.main(["python", "-m", "ai.backend.kernel", "python"])
    assert calls == [
        (
            "/bin/bash",
            [
                "/bin/bash",
                entrypoint.ENTRYPOINT_SCRIPT,
                "python",
                "-m",
                "ai.backend.kernel",
                "python",
            ],
        )
    ]
