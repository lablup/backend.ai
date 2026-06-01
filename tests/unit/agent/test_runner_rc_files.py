"""Tests for the kernel-runner ``.bashrc`` / ``.zshrc`` files.

These rc files are sourced by the in-container shell. When the shell is
non-interactive, sourcing them must not write anything to stdout.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def runner_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "ai" / "backend" / "runner"


@pytest.fixture
def bashrc(runner_dir: Path) -> Path:
    return runner_dir / ".bashrc"


@pytest.fixture
def zshrc(runner_dir: Path) -> Path:
    return runner_dir / ".zshrc"


@pytest.fixture
def shell_env() -> dict[str, str]:
    return {
        "BACKENDAI_PERSISTENT_PATHS": "/home/work/abc",
        "BACKENDAI_CLUSTER_HOST": "main1",
        "BACKENDAI_SESSION_NAME": "test-session",
        "PATH": "/usr/bin:/bin",
        "TERM": "dumb",
    }


class TestRunnerRcStdout:
    def test_bashrc_produces_no_stdout_when_noninteractive(
        self, bashrc: Path, shell_env: dict[str, str]
    ) -> None:
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-c", f"source {bashrc}"],
            env=shell_env,
            capture_output=True,
            timeout=5,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == b"", f"unexpected stdout: {result.stdout!r}"

    @pytest.mark.skipif(shutil.which("zsh") is None, reason="zsh not installed")
    def test_zshrc_produces_no_stdout_when_noninteractive(
        self, zshrc: Path, shell_env: dict[str, str]
    ) -> None:
        result = subprocess.run(
            ["zsh", "--no-rcs", "--no-globalrcs", "-c", f"source {zshrc}"],
            env=shell_env,
            capture_output=True,
            timeout=5,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == b"", f"unexpected stdout: {result.stdout!r}"
