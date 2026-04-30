from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ai.backend.client.cli.v2.deployment.chat.formatter import (
    DeploymentChatFormatter,
    mask_token,
)
from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCacheEntry,
    DeploymentChatConfigEntry,
)


class TestPrintConfig:
    def test_prints_token_masked_and_model_when_set(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        DeploymentChatFormatter.print_config(
            uuid4(),
            DeploymentChatConfigEntry(token="sk-secret", model="llama-3-8b"),
        )
        out = capsys.readouterr().out
        assert "model         : llama-3-8b" in out
        assert "token         : ********" in out
        assert "sk-secret" not in out

    def test_prints_dashes_when_unset(self, capsys: pytest.CaptureFixture[str]) -> None:
        DeploymentChatFormatter.print_config(
            uuid4(),
            DeploymentChatConfigEntry(token=None, model=None),
        )
        out = capsys.readouterr().out
        assert "model         : -" in out
        assert "token         : <unset>" in out


class TestPrintCache:
    def test_prints_endpoint_default_model_and_last_synced(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        DeploymentChatFormatter.print_cache(
            uuid4(),
            DeploymentChatCacheEntry(
                endpoint_url="https://infer.example.test/api",
                default_model="meta/test-model",
                last_synced_at=datetime(2026, 4, 27, 12, 0, tzinfo=UTC),
            ),
        )
        out = capsys.readouterr().out
        assert "endpoint_url  : https://infer.example.test/api" in out
        assert "default_model : meta/test-model" in out
        assert "last_synced_at: 2026-04-27T12:00:00+00:00" in out

    def test_prints_dash_for_missing_default_model(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        DeploymentChatFormatter.print_cache(
            uuid4(),
            DeploymentChatCacheEntry(
                endpoint_url="https://infer.example.test/api",
                default_model=None,
                last_synced_at=datetime(2026, 4, 27, 12, 0, tzinfo=UTC),
            ),
        )
        out = capsys.readouterr().out
        assert "default_model : -" in out


class TestMaskToken:
    def test_mask_long_token_returns_fixed_placeholder(self) -> None:
        # Length-independent placeholder: never leak prefix, suffix, or length.
        assert mask_token("sk-abcdefghijklmnopqrstuvwxyz") == "********"

    def test_mask_short_token_returns_fixed_placeholder(self) -> None:
        assert mask_token("short") == "********"

    def test_mask_none(self) -> None:
        assert mask_token(None) == "<unset>"
