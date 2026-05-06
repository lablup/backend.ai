from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
    DeploymentChatConfigEntry,
    DeploymentChatHistory,
)


@pytest.fixture
def cache() -> DeploymentChatCache:
    return DeploymentChatCache()


@pytest.fixture
def chat_config() -> DeploymentChatConfig:
    return DeploymentChatConfig()


@pytest.fixture
def chat_history() -> DeploymentChatHistory:
    return DeploymentChatHistory()


@pytest.fixture
def history_now() -> datetime:
    return datetime(2026, 4, 27, 12, 0, tzinfo=UTC)


@pytest.fixture
def cache_entry() -> DeploymentChatCacheEntry:
    return DeploymentChatCacheEntry(
        endpoint_url="https://infer.example.test/api",
        default_model=None,
        last_synced_at=datetime(2026, 4, 27, 12, 0, tzinfo=UTC),
    )


@pytest.fixture
def deployment_id() -> UUID:
    return uuid4()


def _entry_with_model(default_model: str | None) -> DeploymentChatCacheEntry:
    return DeploymentChatCacheEntry(
        endpoint_url="https://infer.example.test/api",
        default_model=default_model,
        last_synced_at=datetime(2026, 4, 27, 12, 0, tzinfo=UTC),
    )


class TestCacheMutations:
    def test_set_overwrites_existing_entry(
        self, cache: DeploymentChatCache, deployment_id: UUID
    ) -> None:
        cache.set(deployment_id, _entry_with_model("m1"))
        cache.set(deployment_id, _entry_with_model("m2"))
        stored = cache.get(deployment_id)
        assert stored is not None
        assert stored.default_model == "m2"

    def test_delete_returns_true_when_present(
        self,
        cache: DeploymentChatCache,
        cache_entry: DeploymentChatCacheEntry,
        deployment_id: UUID,
    ) -> None:
        cache.set(deployment_id, cache_entry)
        assert cache.delete(deployment_id) is True
        assert cache.get(deployment_id) is None

    def test_delete_returns_false_when_absent(
        self, cache: DeploymentChatCache, deployment_id: UUID
    ) -> None:
        assert cache.delete(deployment_id) is False


class TestConfigTokenStore:
    def test_set_and_get_token(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-abc")
        assert chat_config.get_token(deployment_id) == "sk-abc"

    def test_set_overwrites_existing_token(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-old")
        chat_config.set_token(deployment_id, "sk-new")
        assert chat_config.get_token(deployment_id) == "sk-new"

    def test_clear_token_returns_true_when_present(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-x")
        assert chat_config.clear_token(deployment_id) is True
        assert chat_config.get_token(deployment_id) is None

    def test_clear_token_returns_false_when_absent(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        assert chat_config.clear_token(deployment_id) is False

    def test_clear_token_keeps_entry_when_model_remains(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-x")
        chat_config.set_model(deployment_id, "llama-3-8b")
        assert chat_config.clear_token(deployment_id) is True
        # Model side of the entry survives token removal.
        entry = chat_config.get(deployment_id)
        assert entry is not None
        assert entry.token is None
        assert entry.model == "llama-3-8b"


class TestConfigModelStore:
    def test_set_and_get_model(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_model(deployment_id, "llama-3-8b")
        assert chat_config.get_model(deployment_id) == "llama-3-8b"

    def test_set_overwrites_existing_model(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_model(deployment_id, "old-model")
        chat_config.set_model(deployment_id, "new-model")
        assert chat_config.get_model(deployment_id) == "new-model"

    def test_clear_model_returns_true_when_present(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_model(deployment_id, "llama-3-8b")
        assert chat_config.clear_model(deployment_id) is True
        assert chat_config.get_model(deployment_id) is None

    def test_clear_model_returns_false_when_absent(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        assert chat_config.clear_model(deployment_id) is False

    def test_token_and_model_share_one_entry(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-x")
        chat_config.set_model(deployment_id, "llama-3-8b")
        entry = chat_config.get(deployment_id)
        assert entry == DeploymentChatConfigEntry(token="sk-x", model="llama-3-8b")


class TestConfigDelete:
    def test_delete_removes_whole_entry(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-x")
        chat_config.set_model(deployment_id, "llama-3-8b")
        assert chat_config.delete(deployment_id) is True
        assert chat_config.get(deployment_id) is None

    def test_delete_returns_false_when_absent(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        assert chat_config.delete(deployment_id) is False


class TestHistoryAppendSlice:
    def test_slice_returns_empty_when_no_entry(
        self, chat_history: DeploymentChatHistory, deployment_id: UUID
    ) -> None:
        assert chat_history.slice(deployment_id, 5) == []

    def test_slice_zero_limit_returns_empty_even_when_populated(
        self,
        chat_history: DeploymentChatHistory,
        deployment_id: UUID,
        history_now: datetime,
    ) -> None:
        chat_history.append(deployment_id, "user", "hi", created_at=history_now)
        chat_history.append(deployment_id, "assistant", "hello", created_at=history_now)
        # Limit 0 lets callers send a turn without context but still record it.
        assert chat_history.slice(deployment_id, 0) == []

    def test_slice_returns_in_insertion_order(
        self,
        chat_history: DeploymentChatHistory,
        deployment_id: UUID,
        history_now: datetime,
    ) -> None:
        for index in range(6):
            chat_history.append(
                deployment_id,
                "user" if index % 2 == 0 else "assistant",
                f"msg-{index}",
                created_at=history_now,
            )
        recent = chat_history.slice(deployment_id, 3)
        assert [m.content for m in recent] == ["msg-3", "msg-4", "msg-5"]

    def test_slice_caps_to_available_length(
        self,
        chat_history: DeploymentChatHistory,
        deployment_id: UUID,
        history_now: datetime,
    ) -> None:
        chat_history.append(deployment_id, "user", "only", created_at=history_now)
        # Asking for more than exists must not error out and must not pad.
        assert [m.content for m in chat_history.slice(deployment_id, 10)] == ["only"]


class TestHistoryTruncation:
    def test_append_drops_oldest_when_max_persisted_exceeded(
        self,
        chat_history: DeploymentChatHistory,
        deployment_id: UUID,
        history_now: datetime,
    ) -> None:
        # FIFO truncation: oldest is dropped first so the most recent
        # context survives across long sessions.
        for index in range(5):
            chat_history.append(
                deployment_id,
                "user",
                f"msg-{index}",
                created_at=history_now,
                max_persisted=3,
            )
        stored = chat_history.get(deployment_id)
        assert stored is not None
        assert [m.content for m in stored] == ["msg-2", "msg-3", "msg-4"]


class TestHistoryClear:
    def test_clear_returns_true_when_present(
        self,
        chat_history: DeploymentChatHistory,
        deployment_id: UUID,
        history_now: datetime,
    ) -> None:
        chat_history.append(deployment_id, "user", "hi", created_at=history_now)
        assert chat_history.clear(deployment_id) is True
        assert chat_history.get(deployment_id) is None

    def test_clear_returns_false_when_absent(
        self,
        chat_history: DeploymentChatHistory,
        deployment_id: UUID,
    ) -> None:
        assert chat_history.clear(deployment_id) is False
