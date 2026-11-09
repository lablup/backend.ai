from __future__ import annotations

from typing import override

from ai.backend.agent.containerd.profile.base import describe_profile_failure
from ai.backend.agent.containerd.profile.runc import RuncProfile


class _Naming(RuncProfile):
    @override
    def describe_failure(self, exit_status: int | None, error_text: str) -> str | None:
        return f"{exit_status}:{error_text}"


class _Raising(RuncProfile):
    @override
    def describe_failure(self, exit_status: int | None, error_text: str) -> str | None:
        raise RuntimeError("boom")


class TestDescribeProfileFailure:
    def test_default_describes_nothing(self) -> None:
        assert describe_profile_failure(RuncProfile(), 1, "x") is None

    def test_profile_text_is_returned(self) -> None:
        assert describe_profile_failure(_Naming(), 137, "gone") == "137:gone"

    def test_failing_hook_describes_nothing(self) -> None:
        assert describe_profile_failure(_Raising(), None, "x") is None
