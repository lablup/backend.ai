from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
)
from ai.backend.client.cli.v2.deployment.chat.utils import (
    load_chat_cache,
    load_chat_config,
    mask_token,
    save_chat_cache,
    save_chat_config,
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


class TestCacheLoadSaveRoundTrip:
    def test_load_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        cache = load_chat_cache(tmp_path / "missing.json")
        assert cache.deployments == {}

    def test_save_then_load_preserves_entry(self, tmp_path: Path) -> None:
        path = tmp_path / "deployment_chat.json"
        cache = DeploymentChatCache()
        dep_id = uuid4()
        original = _make_entry(default_model="gpt-test")
        cache.set(dep_id, original)
        save_chat_cache(cache, path)

        loaded = load_chat_cache(path)
        restored = loaded.deployments[dep_id]
        assert restored.endpoint_url == original.endpoint_url
        assert restored.default_model == original.default_model
        assert restored.last_synced_at == original.last_synced_at


class TestConfigLoadSaveRoundTrip:
    def test_load_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        cfg = load_chat_config(tmp_path / "missing.json")
        assert cfg.tokens == {}

    def test_save_then_load_preserves_tokens(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        cfg = DeploymentChatConfig()
        dep_id = uuid4()
        cfg.set_token(dep_id, "sk-secret-token-1234")
        save_chat_config(cfg, path)

        loaded = load_chat_config(path)
        assert loaded.get_token(dep_id) == "sk-secret-token-1234"


class TestPermissions:
    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_chat_cache_enforces_0600(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = DeploymentChatCache()
        cache.set(uuid4(), _make_entry())
        save_chat_cache(cache, path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_chat_config_enforces_0600(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        cfg = DeploymentChatConfig()
        cfg.set_token(uuid4(), "sk-x")
        save_chat_config(cfg, path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


class TestCacheLoaderResilience:
    def test_load_returns_empty_on_corrupt_json(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text("not-json{", encoding="utf-8")
        assert load_chat_cache(path).deployments == {}

    def test_load_returns_empty_when_top_level_not_object(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text("[]", encoding="utf-8")
        assert load_chat_cache(path).deployments == {}

    def test_load_returns_empty_on_invalid_uuid_key(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text(
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
        assert load_chat_cache(path).deployments == {}

    def test_load_returns_empty_on_malformed_entry_payload(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text(
            json.dumps({
                "deployments": {
                    "12345678-1234-5678-1234-567812345678": {"default_model": "m"},
                },
            }),
            encoding="utf-8",
        )
        assert load_chat_cache(path).deployments == {}


class TestConfigLoaderResilience:
    def test_load_returns_empty_on_corrupt_json(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text("not-json{", encoding="utf-8")
        assert load_chat_config(path).tokens == {}

    def test_load_returns_empty_on_invalid_uuid_key(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps({"tokens": {"not-a-uuid": "sk-x"}}),
            encoding="utf-8",
        )
        assert load_chat_config(path).tokens == {}


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
