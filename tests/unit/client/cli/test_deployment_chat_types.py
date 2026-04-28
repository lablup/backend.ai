from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
)


def _make_entry(
    *,
    endpoint: str = "https://infer.example.test/api",
    default_model: str | None = None,
) -> DeploymentChatCacheEntry:
    return DeploymentChatCacheEntry(
        endpoint_url=endpoint,
        default_model=default_model,
        last_synced_at=datetime(2026, 4, 27, 12, 0, tzinfo=UTC),
    )


class TestEntryFormatSummary:
    def test_format_summary_returns_lines(self) -> None:
        entry = _make_entry(default_model="meta/test-model")
        lines = entry.format_summary()
        assert any("endpoint_url" in line for line in lines)
        assert any("meta/test-model" in line for line in lines)
        assert any("last_synced_at" in line for line in lines)

    def test_format_summary_dash_for_missing_default_model(self) -> None:
        entry = _make_entry(default_model=None)
        lines = entry.format_summary()
        assert any("default_model : -" in line for line in lines)


class TestCacheMutations:
    def test_upsert_overwrites_existing_make_entry(self) -> None:
        cache = DeploymentChatCache()
        dep_id = uuid4()
        cache.upsert(dep_id, _make_entry(default_model="m1"))
        cache.upsert(dep_id, _make_entry(default_model="m2"))
        stored = cache.get(dep_id)
        assert stored is not None
        assert stored.default_model == "m2"

    def test_remove_returns_true_when_present(self) -> None:
        cache = DeploymentChatCache()
        dep_id = uuid4()
        cache.upsert(dep_id, _make_entry())
        assert cache.remove(dep_id) is True
        assert cache.get(dep_id) is None

    def test_remove_returns_false_when_absent(self) -> None:
        assert DeploymentChatCache().remove(uuid4()) is False


class TestConfigTokenStore:
    def test_set_and_get_token(self) -> None:
        cfg = DeploymentChatConfig()
        dep_id = uuid4()
        cfg.set_token(dep_id, "sk-abc")
        assert cfg.get_token(dep_id) == "sk-abc"

    def test_set_overwrites_existing_token(self) -> None:
        cfg = DeploymentChatConfig()
        dep_id = uuid4()
        cfg.set_token(dep_id, "sk-old")
        cfg.set_token(dep_id, "sk-new")
        assert cfg.get_token(dep_id) == "sk-new"

    def test_clear_token_returns_true_when_present(self) -> None:
        cfg = DeploymentChatConfig()
        dep_id = uuid4()
        cfg.set_token(dep_id, "sk-x")
        assert cfg.clear_token(dep_id) is True
        assert cfg.get_token(dep_id) is None

    def test_clear_token_returns_false_when_absent(self) -> None:
        assert DeploymentChatConfig().clear_token(uuid4()) is False
