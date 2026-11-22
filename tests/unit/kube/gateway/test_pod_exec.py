from __future__ import annotations

import pytest

from ai.backend.kube.gateway.pod_exec import _exit_code


class TestExitCode:
    @pytest.mark.parametrize(
        ("status", "code"),
        [
            (b"", 0),
            (b'{"status":"Success"}', 0),
            (
                b'{"status":"Failure","reason":"NonZeroExitCode",'
                b'"details":{"causes":[{"reason":"ExitCode","message":"3"}]}}',
                3,
            ),
            (b'{"status":"Failure","message":"container not found"}', -1),
        ],
        ids=["no-status", "success", "non-zero", "exec-failed"],
    )
    def test_parses_status_channel(self, status: bytes, code: int) -> None:
        assert _exit_code(status) == code
