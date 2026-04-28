from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from ai.backend.client.cli.v2.deployment.chat import utils as chat_utils
from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
)
from ai.backend.client.cli.v2.deployment.chat.utils import (
    mask_token,
    save_chat_cache,
    save_chat_config,
)


@pytest.fixture
def cache_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "deployment_chat.json"
    monkeypatch.setattr(chat_utils, "CHAT_CACHE_FILE", path)
    return path


@pytest.fixture
def config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "deployment_chat_config.json"
    monkeypatch.setattr(chat_utils, "CHAT_CONFIG_FILE", path)
    return path


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


class TestCacheLoadSaveRoundTrip:
    def test_load_returns_empty_when_file_missing(self, cache_path: Path) -> None:
        assert DeploymentChatCache.load().deployments == {}

    def test_save_then_load_preserves_entry(self, cache_path: Path) -> None:
        cache = DeploymentChatCache()
        dep_id = uuid4()
        original = _make_entry(default_model="gpt-test")
        cache.set(dep_id, original)
        save_chat_cache(cache)

        loaded = DeploymentChatCache.load()
        restored = loaded.deployments[dep_id]
        assert restored.endpoint_url == original.endpoint_url
        assert restored.default_model == original.default_model
        assert restored.last_synced_at == original.last_synced_at


class TestConfigLoadSaveRoundTrip:
    def test_load_returns_empty_when_file_missing(self, config_path: Path) -> None:
        assert DeploymentChatConfig.load().tokens == {}

    def test_save_then_load_preserves_tokens(self, config_path: Path) -> None:
        cfg = DeploymentChatConfig()
        dep_id = uuid4()
        cfg.set_token(dep_id, "sk-secret-token-1234")
        save_chat_config(cfg)

        loaded = DeploymentChatConfig.load()
        assert loaded.get_token(dep_id) == "sk-secret-token-1234"


class TestPermissions:
    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_chat_cache_enforces_0600(self, cache_path: Path) -> None:
        cache = DeploymentChatCache()
        cache.set(uuid4(), _make_entry())
        save_chat_cache(cache)
        assert stat.S_IMODE(cache_path.stat().st_mode) == 0o600

    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_chat_config_enforces_0600(self, config_path: Path) -> None:
        cfg = DeploymentChatConfig()
        cfg.set_token(uuid4(), "sk-x")
        save_chat_config(cfg)
        assert stat.S_IMODE(config_path.stat().st_mode) == 0o600


class TestCacheLoaderResilience:
    def test_load_returns_empty_on_corrupt_json(self, cache_path: Path) -> None:
        cache_path.write_text("not-json{", encoding="utf-8")
        assert DeploymentChatCache.load().deployments == {}

    def test_load_returns_empty_when_top_level_not_object(self, cache_path: Path) -> None:
        cache_path.write_text("[]", encoding="utf-8")
        assert DeploymentChatCache.load().deployments == {}

    def test_load_returns_empty_on_invalid_uuid_key(self, cache_path: Path) -> None:
        cache_path.write_text(
            json.dumps({
                "deployments": {
                    "not-a-uuid": {
                        "endpoint_url": "https://x.example",
                        "default_model": None,
                        "last_synced_at": "2026-04-27T12:00:00+00:00",
                    },
                },
            }),
            encoding="utf-8",
        )
        assert DeploymentChatCache.load().deployments == {}

    def test_load_returns_empty_on_malformed_entry_payload(self, cache_path: Path) -> None:
        cache_path.write_text(
            json.dumps({
                "deployments": {
                    "12345678-1234-5678-1234-567812345678": {"default_model": "m"},
                },
            }),
            encoding="utf-8",
        )
        assert DeploymentChatCache.load().deployments == {}


class TestConfigLoaderResilience:
    def test_load_returns_empty_on_corrupt_json(self, config_path: Path) -> None:
        config_path.write_text("not-json{", encoding="utf-8")
        assert DeploymentChatConfig.load().tokens == {}

    def test_load_returns_empty_on_invalid_uuid_key(self, config_path: Path) -> None:
        config_path.write_text(
            json.dumps({"tokens": {"not-a-uuid": "sk-x"}}),
            encoding="utf-8",
        )
        assert DeploymentChatConfig.load().tokens == {}


class TestMaskToken:
    def test_mask_long_token(self) -> None:
        masked = mask_token("sk-abcdefghijklmnopqrstuvwxyz")
        assert masked.startswith("sk-")
        assert masked.endswith("wxyz")
        assert "***" in masked

    def test_mask_short_token(self) -> None:
        assert mask_token("short") == "***"

    def test_mask_none(self) -> None:
        assert mask_token(None) == "<unset>"
