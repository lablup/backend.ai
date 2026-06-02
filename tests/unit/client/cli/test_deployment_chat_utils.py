from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from ai.backend.client.cli.v2.deployment.chat import types as chat_types
from ai.backend.client.cli.v2.deployment.chat import utils as chat_utils
from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
    DeploymentChatHistory,
)


@pytest.fixture
def cache_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "deployment_chat" / "cache.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Both ``utils`` (where the path constant lives) and ``types`` (which
    # imported it at module load time) must see the redirected path.
    monkeypatch.setattr(chat_utils, "CHAT_CACHE_FILE", path)
    monkeypatch.setattr(chat_types, "CHAT_CACHE_FILE", path)
    return path


@pytest.fixture
def config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "deployment_chat" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(chat_utils, "CHAT_CONFIG_FILE", path)
    monkeypatch.setattr(chat_types, "CHAT_CONFIG_FILE", path)
    return path


@pytest.fixture
def history_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "deployment_chat" / "history.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(chat_utils, "CHAT_HISTORY_FILE", path)
    monkeypatch.setattr(chat_types, "CHAT_HISTORY_FILE", path)
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
        cache.save()

        loaded = DeploymentChatCache.load()
        restored = loaded.deployments[dep_id]
        assert restored.endpoint_url == original.endpoint_url
        assert restored.default_model == original.default_model
        assert restored.last_synced_at == original.last_synced_at


class TestConfigLoadSaveRoundTrip:
    def test_load_returns_empty_when_file_missing(self, config_path: Path) -> None:
        assert DeploymentChatConfig.load().deployments == {}

    def test_save_then_load_preserves_token_and_model(self, config_path: Path) -> None:
        cfg = DeploymentChatConfig()
        dep_id = uuid4()
        cfg.set_token(dep_id, "sk-secret-token-1234")
        cfg.set_model(dep_id, "llama-3-8b-instruct")
        cfg.save()

        loaded = DeploymentChatConfig.load()
        assert loaded.get_token(dep_id) == "sk-secret-token-1234"
        assert loaded.get_model(dep_id) == "llama-3-8b-instruct"


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
        assert DeploymentChatConfig.load().deployments == {}

    def test_load_returns_empty_on_invalid_uuid_key(self, config_path: Path) -> None:
        config_path.write_text(
            json.dumps({
                "deployments": {"not-a-uuid": {"token": "sk-x", "model": None}},
            }),
            encoding="utf-8",
        )
        assert DeploymentChatConfig.load().deployments == {}


class TestHistoryLoadSaveRoundTrip:
    def test_load_returns_empty_when_file_missing(self, history_path: Path) -> None:
        assert DeploymentChatHistory.load().deployments == {}

    def test_save_then_load_preserves_messages(self, history_path: Path) -> None:
        history = DeploymentChatHistory()
        dep_id = uuid4()
        now = datetime(2026, 4, 27, 12, 0, tzinfo=UTC)
        history.append(dep_id, "user", "hello", created_at=now)
        history.append(dep_id, "assistant", "world", created_at=now)
        history.save()

        loaded = DeploymentChatHistory.load()
        messages = loaded.get(dep_id)
        assert messages is not None
        assert [(m.role, m.content) for m in messages] == [
            ("user", "hello"),
            ("assistant", "world"),
        ]
        assert messages[0].created_at == now


class TestHistoryLoaderResilience:
    def test_load_returns_empty_on_corrupt_json(self, history_path: Path) -> None:
        history_path.write_text("not-json{", encoding="utf-8")
        assert DeploymentChatHistory.load().deployments == {}

    def test_load_returns_empty_when_top_level_not_object(self, history_path: Path) -> None:
        history_path.write_text("[]", encoding="utf-8")
        assert DeploymentChatHistory.load().deployments == {}

    def test_load_returns_empty_on_invalid_uuid_key(self, history_path: Path) -> None:
        history_path.write_text(
            json.dumps({
                "deployments": {
                    "not-a-uuid": [
                        {
                            "role": "user",
                            "content": "hi",
                            "created_at": "2026-04-27T12:00:00+00:00",
                        },
                    ],
                },
            }),
            encoding="utf-8",
        )
        assert DeploymentChatHistory.load().deployments == {}

    def test_load_returns_empty_on_malformed_message_payload(self, history_path: Path) -> None:
        history_path.write_text(
            json.dumps({
                "deployments": {
                    "12345678-1234-5678-1234-567812345678": [{"role": "user"}],
                },
            }),
            encoding="utf-8",
        )
        assert DeploymentChatHistory.load().deployments == {}
