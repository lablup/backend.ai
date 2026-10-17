from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

from ai.backend.kernel import _reexec_with_argv0


@pytest.mark.parametrize("virtual_env", [None, "/opt/some-venv"])
def test_reexec_sets_pythonhome_regardless_of_virtual_env(
    virtual_env: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BACKEND_REEXECED", raising=False)
    monkeypatch.delenv("PYTHONHOME", raising=False)
    if virtual_env is None:
        monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    else:
        monkeypatch.setenv("VIRTUAL_ENV", virtual_env)
    with patch("os.execvpe") as mock_exec:
        _reexec_with_argv0("bai-krunner")
    mock_exec.assert_called_once()
    _, argv, env = mock_exec.call_args.args
    assert argv[0] == "bai-krunner"
    assert env["BACKEND_REEXECED"] == "1"
    assert env["PYTHONHOME"] == sys.prefix
    if virtual_env is not None:
        assert env["VIRTUAL_ENV"] == virtual_env
    os.unlink(f"/tmp/{os.getpid()}.krunner-args")
