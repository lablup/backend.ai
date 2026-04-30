from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.client.cli.v2.deployment.chat.formatter import (
    DeploymentChatFormatter,
    mask_token,
)
from ai.backend.client.cli.v2.deployment.chat.types import DeploymentChatCacheEntry


def _make_entry(
    *,
    default_model: str | None = None,
) -> DeploymentChatCacheEntry:
    return DeploymentChatCacheEntry(
        endpoint_url="https://infer.example.test/api",
        default_model=default_model,
        last_synced_at=datetime(2026, 4, 27, 12, 0, tzinfo=UTC),
    )


class TestEntryLines:
    def test_returns_lines_for_present_entry(self) -> None:
        lines = DeploymentChatFormatter.entry_lines(_make_entry(default_model="meta/test"))
        assert any("endpoint_url" in line for line in lines)
        assert any("meta/test" in line for line in lines)
        assert any("last_synced_at" in line for line in lines)

    def test_dash_for_missing_default_model(self) -> None:
        lines = DeploymentChatFormatter.entry_lines(_make_entry(default_model=None))
        assert any("default_model : -" in line for line in lines)

    def test_all_dashes_when_entry_is_none(self) -> None:
        lines = DeploymentChatFormatter.entry_lines(None)
        assert lines == [
            "endpoint_url  : -",
            "default_model : -",
            "last_synced_at: -",
        ]


class TestMaskToken:
    def test_mask_long_token_returns_fixed_placeholder(self) -> None:
        # Length-independent placeholder: never leak prefix, suffix, or length.
        assert mask_token("sk-abcdefghijklmnopqrstuvwxyz") == "********"

    def test_mask_short_token_returns_fixed_placeholder(self) -> None:
        assert mask_token("short") == "********"

    def test_mask_none(self) -> None:
        assert mask_token(None) == "<unset>"
