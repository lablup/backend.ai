from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
    DeploymentChatConfigEntry,
)


@pytest.fixture
def cache() -> DeploymentChatCache:
    return DeploymentChatCache()


@pytest.fixture
def chat_config() -> DeploymentChatConfig:
    return DeploymentChatConfig()


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

    def test_pop_returns_true_when_present(
        self,
        cache: DeploymentChatCache,
        cache_entry: DeploymentChatCacheEntry,
        deployment_id: UUID,
    ) -> None:
        cache.set(deployment_id, cache_entry)
        assert cache.pop(deployment_id) is True
        assert cache.get(deployment_id) is None

    def test_pop_returns_false_when_absent(
        self, cache: DeploymentChatCache, deployment_id: UUID
    ) -> None:
        assert cache.pop(deployment_id) is False


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

    def test_pop_token_returns_true_when_present(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-x")
        assert chat_config.pop_token(deployment_id) is True
        assert chat_config.get_token(deployment_id) is None

    def test_pop_token_returns_false_when_absent(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        assert chat_config.pop_token(deployment_id) is False

    def test_pop_token_keeps_entry_when_model_remains(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-x")
        chat_config.set_model(deployment_id, "llama-3-8b")
        assert chat_config.pop_token(deployment_id) is True
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

    def test_pop_model_returns_true_when_present(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_model(deployment_id, "llama-3-8b")
        assert chat_config.pop_model(deployment_id) is True
        assert chat_config.get_model(deployment_id) is None

    def test_pop_model_returns_false_when_absent(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        assert chat_config.pop_model(deployment_id) is False

    def test_token_and_model_share_one_entry(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-x")
        chat_config.set_model(deployment_id, "llama-3-8b")
        entry = chat_config.get(deployment_id)
        assert entry == DeploymentChatConfigEntry(token="sk-x", model="llama-3-8b")


class TestConfigPop:
    def test_pop_removes_whole_entry(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        chat_config.set_token(deployment_id, "sk-x")
        chat_config.set_model(deployment_id, "llama-3-8b")
        assert chat_config.pop(deployment_id) is True
        assert chat_config.get(deployment_id) is None

    def test_pop_returns_false_when_absent(
        self, chat_config: DeploymentChatConfig, deployment_id: UUID
    ) -> None:
        assert chat_config.pop(deployment_id) is False
