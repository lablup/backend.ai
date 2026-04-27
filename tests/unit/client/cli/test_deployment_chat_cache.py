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
    save_chat_cache,
)


def _entry(
    *,
    endpoint: str = "https://infer.example.test/api",
    default_model: str | None = None,
) -> DeploymentChatCacheEntry:
    return DeploymentChatCacheEntry(
        endpoint_url=endpoint,
        default_model=default_model,
        last_synced_at=datetime(2026, 4, 27, 12, 0, tzinfo=UTC),
    )


class TestLoadSaveRoundTrip:
    def test_load_returns_empty_cache_when_file_missing(self, tmp_path: Path) -> None:
        cache = load_chat_cache(tmp_path / "missing.json")
        assert cache.deployments == {}

    def test_save_then_load_preserves_entry(self, tmp_path: Path) -> None:
        path = tmp_path / "deployment_chat.json"
        cache = DeploymentChatCache()
        dep_id = uuid4()
        original = _entry(default_model="gpt-test")
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


class TestPermissions:
    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission check")
    def test_save_enforces_0600(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = DeploymentChatCache()
        cache.upsert(uuid4(), _entry())
        save_chat_cache(cache, path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


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


class TestLoaderResilience:
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


class TestEntryMutations:
    def test_upsert_overwrites_existing_entry(self) -> None:
        cache = DeploymentChatCache()
        dep_id = uuid4()
        cache.upsert(dep_id, _entry(default_model="m1"))
        cache.upsert(dep_id, _entry(default_model="m2"))
        stored = cache.get(dep_id)
        assert stored is not None
        assert stored.default_model == "m2"

    def test_remove_returns_true_when_present(self) -> None:
        cache = DeploymentChatCache()
        dep_id = uuid4()
        cache.upsert(dep_id, _entry())
        assert cache.remove(dep_id) is True
        assert cache.get(dep_id) is None

    def test_remove_returns_false_when_absent(self) -> None:
        assert DeploymentChatCache().remove(uuid4()) is False
