from __future__ import annotations

from uuid import uuid4

import pytest

from ai.backend.client.cli.v2.deployment.chat.formatter import (
    DeploymentChatFormatter,
    mask_token,
)
from ai.backend.client.cli.v2.deployment.chat.types import DeploymentChatConfigEntry


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


class TestMaskToken:
    def test_mask_long_token_returns_fixed_placeholder(self) -> None:
        # Length-independent placeholder: never leak prefix, suffix, or length.
        assert mask_token("sk-abcdefghijklmnopqrstuvwxyz") == "********"

    def test_mask_short_token_returns_fixed_placeholder(self) -> None:
        assert mask_token("short") == "********"

    def test_mask_none(self) -> None:
        assert mask_token(None) == "<unset>"
