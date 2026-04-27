from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from ai.backend.client.cli.v2.deployment_chat_cache import (
    CHAT_CACHE_SCHEMA_VERSION,
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    IncompatibleChatCacheError,
    load_chat_cache,
    mask_token,
    save_chat_cache,
)


def _entry(
    *,
    endpoint: str = "https://infer.example.test/api",
    api_key: str | None = "sk-secret-token-value-1234",
    default_model: str | None = None,
) -> DeploymentChatCacheEntry:
    return DeploymentChatCacheEntry(
        endpoint_url=endpoint,
        vllm_api_key=api_key,
        default_model=default_model,
        last_synced_at=datetime(2026, 4, 27, 12, 0, tzinfo=UTC),
    )


class TestLoadSaveRoundTrip:
    def test_load_returns_empty_cache_when_file_missing(self, tmp_path: Path) -> None:
        cache = load_chat_cache(tmp_path / "missing.json")
        assert cache.entries == {}

    def test_save_then_load_preserves_entry(self, tmp_path: Path) -> None:
        path = tmp_path / "deployment_chat.json"
        cache = DeploymentChatCache()
        dep_id = uuid4()
        original = _entry()
        cache.upsert(dep_id, original)
        save_chat_cache(cache, path)

        loaded = load_chat_cache(path)
        assert dep_id in loaded.entries
        restored = loaded.entries[dep_id]
        assert restored.endpoint_url == original.endpoint_url
        assert restored.vllm_api_key == original.vllm_api_key
        assert restored.default_model == original.default_model
        assert restored.last_synced_at == original.last_synced_at

    def test_save_writes_schema_version(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        save_chat_cache(DeploymentChatCache(), path)
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["schema_version"] == CHAT_CACHE_SCHEMA_VERSION

    def test_load_skips_invalid_uuid_keys(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text(
            json.dumps({
                "schema_version": CHAT_CACHE_SCHEMA_VERSION,
                "deployments": {
                    "not-a-uuid": {
                        "endpoint_url": "https://x.example",
                        "vllm_api_key": None,
                        "default_model": None,
                        "last_synced_at": "2026-04-27T12:00:00+00:00",
                    },
                },
            }),
            encoding="utf-8",
        )
        loaded = load_chat_cache(path)
        assert loaded.entries == {}


class TestPermissions:
    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_enforces_0600(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = DeploymentChatCache()
        cache.upsert(uuid4(), _entry())
        save_chat_cache(cache, path)
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600

    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_resets_too_open_permissions(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text("{}", encoding="utf-8")
        os.chmod(path, 0o644)
        cache = DeploymentChatCache()
        cache.upsert(uuid4(), _entry())
        save_chat_cache(cache, path)
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600


class TestSchemaVersionGuard:
    def test_load_rejects_newer_schema_version(self, tmp_path: Path) -> None:
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


class TestUpsertAndRemove:
    def test_upsert_overwrites_existing_entry(self) -> None:
        cache = DeploymentChatCache()
        dep_id = uuid4()
        cache.upsert(dep_id, _entry(api_key="sk-old-token-1234"))
        cache.upsert(dep_id, _entry(api_key="sk-new-token-5678"))
        stored = cache.get(dep_id)
        assert stored is not None
        assert stored.vllm_api_key == "sk-new-token-5678"

    def test_remove_returns_true_when_present(self) -> None:
        cache = DeploymentChatCache()
        dep_id = uuid4()
        cache.upsert(dep_id, _entry())
        assert cache.remove(dep_id) is True
        assert cache.get(dep_id) is None

    def test_remove_returns_false_when_absent(self) -> None:
        cache = DeploymentChatCache()
        assert cache.remove(uuid4()) is False


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


class TestAtomicWrite:
    def test_save_does_not_leave_temp_files_on_success(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = DeploymentChatCache()
        cache.upsert(uuid4(), _entry())
        save_chat_cache(cache, path)
        leftover = [p for p in tmp_path.iterdir() if p.name.startswith("cache.json.")]
        assert leftover == []


class TestEntryFromDictTolerance:
    def test_from_dict_accepts_missing_optional_fields(self) -> None:
        entry = DeploymentChatCacheEntry.from_dict({
            "endpoint_url": "https://infer.example.test/api",
        })
        assert entry.endpoint_url == "https://infer.example.test/api"
        assert entry.vllm_api_key is None
        assert entry.default_model is None
        assert isinstance(entry.last_synced_at, datetime)


class TestLoadInvalidShapes:
    def test_load_returns_empty_when_top_level_not_object(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text("[]", encoding="utf-8")
        loaded = load_chat_cache(path)
        assert loaded.entries == {}

    def test_load_handles_uuid_keyed_entry(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        dep_id = UUID("12345678-1234-5678-1234-567812345678")
        path.write_text(
            json.dumps({
                "schema_version": CHAT_CACHE_SCHEMA_VERSION,
                "deployments": {
                    str(dep_id): {
                        "endpoint_url": "https://infer.example.test/api",
                        "vllm_api_key": "sk-token-value-1234",
                        "default_model": "gpt-test",
                        "last_synced_at": "2026-04-27T12:00:00+00:00",
                    },
                },
            }),
            encoding="utf-8",
        )
        loaded = load_chat_cache(path)
        assert dep_id in loaded.entries
        assert loaded.entries[dep_id].default_model == "gpt-test"
