from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from ai.backend.kernel import _reexec_with_argv0


@pytest.mark.parametrize("virtual_env", [None, "/opt/some-venv"])
def test_reexec_sets_pythonhome(monkeypatch: pytest.MonkeyPatch, virtual_env: str | None) -> None:
    monkeypatch.delenv("BACKEND_REEXECED", raising=False)
    if virtual_env is None:
        monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    else:
        monkeypatch.setenv("VIRTUAL_ENV", virtual_env)
    with patch("os.execvpe") as mock_exec, patch("pathlib.Path.write_text"):
        _reexec_with_argv0("bai-krunner")
    _, _, env = mock_exec.call_args.args
    assert env["PYTHONHOME"] == sys.base_prefix
