from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast, override

from ai.backend.agent.containerd.profile.base import RuntimeProfile, summarize_profile_attestation
from ai.backend.agent.containerd.profile.runc import RuncProfile

from .conftest import FakeProfile


class _SummarizingProfile(FakeProfile):
    calls: list[tuple[str, int, float]]
    _summary: Mapping[str, Any] | None

    def __init__(self, summary: Mapping[str, Any] | None) -> None:
        super().__init__("summarizing", accepts=True)
        self._summary = summary
        self.calls = []

    @override
    async def summarize_attestation(
        self, host: str, port: int, timeout_s: float
    ) -> Mapping[str, Any] | None:
        self.calls.append((host, port, timeout_s))
        return self._summary


class _RaisingProfile(FakeProfile):
    def __init__(self) -> None:
        super().__init__("raising", accepts=True)

    @override
    async def summarize_attestation(
        self, host: str, port: int, timeout_s: float
    ) -> Mapping[str, Any] | None:
        raise RuntimeError("buggy profile")


class _TwoMethodProfile:
    name = "two-method"

    def accepts(self, slots: Any) -> bool:
        return True

    def plan(self, kernel: Any) -> Any:
        raise AssertionError("must not run")


class TestSummarizeProfileAttestation:
    async def test_runc_summarizes_nothing(self) -> None:
        assert await summarize_profile_attestation(RuncProfile(1.0), "h", 1, 1.0) is None

    async def test_profile_summary_is_returned(self) -> None:
        profile = _SummarizingProfile({"attested": True})

        assert await summarize_profile_attestation(profile, "h", 8080, 2.0) == {"attested": True}
        assert profile.calls == [("h", 8080, 2.0)]

    async def test_two_method_profile_summarizes_nothing(self) -> None:
        profile = cast(RuntimeProfile, _TwoMethodProfile())

        assert await summarize_profile_attestation(profile, "h", 1, 1.0) is None

    async def test_raising_profile_summarizes_nothing(self) -> None:
        assert await summarize_profile_attestation(_RaisingProfile(), "h", 1, 1.0) is None
