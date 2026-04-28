from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
    IncompatibleChatCacheError,
    IncompatibleChatConfigError,
)
from ai.backend.client.cli.v2.deployment.chat.utils import (
    CHAT_CACHE_SCHEMA_VERSION,
    CHAT_CONFIG_SCHEMA_VERSION,
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

    def test_save_then_load_preserves_make_entry(self, tmp_path: Path) -> None:
        path = tmp_path / "deployment_chat.json"
        cache = DeploymentChatCache()
        dep_id = uuid4()
        original = _make_entry(default_model="gpt-test")
        cache.upsert(dep_id, original)
        save_chat_cache(cache, path)

        loaded = load_chat_cache(path)
        restored = loaded.deployments[dep_id]
        assert restored.endpoint_url == original.endpoint_url
        assert restored.default_model == original.default_model
        assert restored.last_synced_at == original.last_synced_at

    def test_save_writes_schema_version(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        save_chat_cache(DeploymentChatCache(), path)
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["schema_version"] == CHAT_CACHE_SCHEMA_VERSION
        assert payload["deployments"] == {}


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

    def test_save_writes_schema_version(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        save_chat_config(DeploymentChatConfig(), path)
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["schema_version"] == CHAT_CONFIG_SCHEMA_VERSION
        assert payload["tokens"] == {}


class TestPermissions:
    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_chat_cache_enforces_0600(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = DeploymentChatCache()
        cache.upsert(uuid4(), _make_entry())
        save_chat_cache(cache, path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_chat_config_enforces_0600(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        cfg = DeploymentChatConfig()
        cfg.set_token(uuid4(), "sk-x")
        save_chat_config(cfg, path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


class TestSchemaVersionGuard:
    def test_load_chat_cache_rejects_newer_schema(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text(
            json.dumps({
                "schema_version": CHAT_CACHE_SCHEMA_VERSION + 1,
                "deployments": {},
            }),
            encoding="utf-8",
        )
        with pytest.raises(IncompatibleChatCacheError):
            load_chat_cache(path)

    def test_load_chat_config_rejects_newer_schema(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps({
                "schema_version": CHAT_CONFIG_SCHEMA_VERSION + 1,
                "tokens": {},
            }),
            encoding="utf-8",
        )
        with pytest.raises(IncompatibleChatConfigError):
            load_chat_config(path)


class TestCacheLoaderResilience:
    def test_load_returns_empty_on_corrupt_json(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text("not-json{", encoding="utf-8")
        assert load_chat_cache(path).deployments == {}

    def test_load_returns_empty_when_top_level_not_object(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text("[]", encoding="utf-8")
        assert load_chat_cache(path).deployments == {}

    def test_load_skips_invalid_uuid_keys(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        good_id = UUID("12345678-1234-5678-1234-567812345678")
        path.write_text(
            json.dumps({
                "schema_version": CHAT_CACHE_SCHEMA_VERSION,
                "deployments": {
                    "not-a-uuid": {
                        "endpoint_url": "https://x.example",
                        "default_model": None,
                        "last_synced_at": "2026-04-27T12:00:00+00:00",
                    },
                    str(good_id): {
                        "endpoint_url": "https://y.example",
                        "default_model": "m",
                        "last_synced_at": "2026-04-27T12:00:00+00:00",
                    },
                },
            }),
            encoding="utf-8",
        )
        loaded = load_chat_cache(path)
        assert list(loaded.deployments.keys()) == [good_id]

    def test_load_skips_malformed_entry_payload(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        good_id = UUID("12345678-1234-5678-1234-567812345678")
        bad_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        path.write_text(
            json.dumps({
                "schema_version": CHAT_CACHE_SCHEMA_VERSION,
                "deployments": {
                    str(bad_id): {"default_model": "m"},
                    str(good_id): {
                        "endpoint_url": "https://y.example",
                        "default_model": "m",
                        "last_synced_at": "2026-04-27T12:00:00+00:00",
                    },
                },
            }),
            encoding="utf-8",
        )
        loaded = load_chat_cache(path)
        assert list(loaded.deployments.keys()) == [good_id]


class TestConfigLoaderResilience:
    def test_load_returns_empty_on_corrupt_json(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text("not-json{", encoding="utf-8")
        assert load_chat_config(path).tokens == {}

    def test_load_skips_invalid_uuid_keys(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        good_id = UUID("12345678-1234-5678-1234-567812345678")
        path.write_text(
            json.dumps({
                "schema_version": CHAT_CONFIG_SCHEMA_VERSION,
                "tokens": {
                    "not-a-uuid": "sk-x",
                    str(good_id): "sk-y",
                },
            }),
            encoding="utf-8",
        )
        loaded = load_chat_config(path)
        assert loaded.tokens == {good_id: "sk-y"}


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
