"""User-managed config for ``./bai deployment chat-config`` (API keys per deployment).

Stores the inference API keys the user explicitly registered through
``./bai deployment chat-config set``. Distinct from the auto-managed
endpoint cache so that token registration is never accidentally
clobbered when the cache is refreshed.

Persisted as a JSON file at ``~/.backend.ai/deployment_chat_config.json``
with ``0600`` permissions because the API keys are stored in plaintext.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.client.cli.v2.helpers import CONFIG_DIR

CHAT_CONFIG_FILE = CONFIG_DIR / "deployment_chat_config.json"
CHAT_CONFIG_SCHEMA_VERSION = 1


class DeploymentChatConfig(BaseModel):
    """Per-deployment API key registry (user-managed)."""

    schema_version: int = Field(default=CHAT_CONFIG_SCHEMA_VERSION)
    tokens: dict[UUID, str] = Field(default_factory=dict)

    def get_token(self, deployment_id: UUID) -> str | None:
        return self.tokens.get(deployment_id)

    def set_token(self, deployment_id: UUID, token: str) -> None:
        self.tokens[deployment_id] = token

    def clear_token(self, deployment_id: UUID) -> bool:
        return self.tokens.pop(deployment_id, None) is not None


class IncompatibleChatConfigError(Exception):
    """Raised when the on-disk config file uses a newer schema than this build."""


def load_chat_config(path: Path = CHAT_CONFIG_FILE) -> DeploymentChatConfig:
    """Load the chat config; return an empty config when the file is absent or unreadable."""
    if not path.exists():
        return DeploymentChatConfig()
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return DeploymentChatConfig()
    if not isinstance(raw, dict):
        return DeploymentChatConfig()
    schema = raw.get("schema_version")
    if schema is not None and isinstance(schema, int) and schema > CHAT_CONFIG_SCHEMA_VERSION:
        raise IncompatibleChatConfigError(
            f"deployment_chat_config.json schema version {schema} is newer than supported "
            f"{CHAT_CONFIG_SCHEMA_VERSION}; please upgrade the client."
        )
    tokens: dict[UUID, str] = {}
    tokens_raw = raw.get("tokens") or {}
    if isinstance(tokens_raw, dict):
        for key, value in tokens_raw.items():
            try:
                dep_id = UUID(str(key))
            except ValueError:
                continue
            if isinstance(value, str):
                tokens[dep_id] = value
    return DeploymentChatConfig(tokens=tokens)


def save_chat_config(config: DeploymentChatConfig, path: Path = CHAT_CONFIG_FILE) -> None:
    """Atomically write the chat config and enforce ``0600`` permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = config.model_dump_json(indent=2)
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        tmp_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        tmp_path.replace(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def mask_token(token: str | None) -> str:
    """Render a token as ``sk-***...***xxxx`` for diagnostic display."""
    if token is None:
        return "<unset>"
    if len(token) <= 8:
        return "***"
    return f"{token[:3]}***...***{token[-4:]}"
