from __future__ import annotations

from collections.abc import Mapping
from typing import Any, override

from ai.backend.agent.containerd.profile.base import summarize_profile_attestation
from ai.backend.agent.containerd.profile.runc import RuncProfile


class _Summarizing(RuncProfile):
    @override
    async def summarize_attestation(
        self, host: str, port: int, timeout_s: float
    ) -> Mapping[str, Any] | None:
        return {"endpoint": f"{host}:{port}", "timeout": timeout_s}


class _Raising(RuncProfile):
    @override
    async def summarize_attestation(
        self, host: str, port: int, timeout_s: float
    ) -> Mapping[str, Any] | None:
        raise RuntimeError("boom")


class TestSummarizeProfileAttestation:
    async def test_default_summarizes_nothing(self) -> None:
        assert await summarize_profile_attestation(RuncProfile(), "h", 1, 1.0) is None

    async def test_profile_summary_is_returned(self) -> None:
        summary = await summarize_profile_attestation(_Summarizing(), "h", 8080, 2.0)

        assert summary == {"endpoint": "h:8080", "timeout": 2.0}

    async def test_failing_hook_summarizes_nothing(self) -> None:
        assert await summarize_profile_attestation(_Raising(), "h", 1, 1.0) is None
