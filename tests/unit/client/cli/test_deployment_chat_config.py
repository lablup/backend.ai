from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from ai.backend.client.cli.v2.deployment_chat_config import (
    CHAT_CONFIG_SCHEMA_VERSION,
    DeploymentChatConfig,
    IncompatibleChatConfigError,
    load_chat_config,
    mask_token,
    save_chat_config,
)


class TestLoadSaveRoundTrip:
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
    def test_save_enforces_0600(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        cfg = DeploymentChatConfig()
        cfg.set_token(uuid4(), "sk-x")
        save_chat_config(cfg, path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


class TestSchemaVersionGuard:
    def test_load_rejects_newer_schema_version(self, tmp_path: Path) -> None:
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


class TestLoaderResilience:
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


class TestTokenStore:
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
