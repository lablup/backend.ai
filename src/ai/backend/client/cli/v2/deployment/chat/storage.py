"""Disk persistence for ``./bai deployment chat`` data types.

Pure data types live in :mod:`ai.backend.common.data.deployment_chat`; this
module wires them to ``~/.backend.ai/deployment_chat/*.json`` files. Keeping
load/save here (instead of as classmethods on the data types) avoids a
backward dependency from ``common`` to ``client.cli`` and lets non-CLI
consumers reuse the data types without dragging the CLI's filesystem layout.
"""

from __future__ import annotations

import sys

from pydantic import ValidationError

from ai.backend.client.cli.v2.deployment.chat.utils import (
    CHAT_CACHE_FILE,
    CHAT_CONFIG_FILE,
    read_json_file,
    write_json_file,
)
from ai.backend.common.data.deployment_chat import (
    DeploymentChatCache,
    DeploymentChatConfig,
)


def load_chat_cache() -> DeploymentChatCache:
    """Load the chat cache; return an empty cache when the file is absent or unreadable."""
    raw = read_json_file(CHAT_CACHE_FILE)
    if raw is None:
        return DeploymentChatCache()
    try:
        return DeploymentChatCache.model_validate(raw)
    except ValidationError:
        print(
            f"WARNING: {CHAT_CACHE_FILE} is in an invalid format and was ignored.",
            file=sys.stderr,
        )
        return DeploymentChatCache()


def save_chat_cache(cache: DeploymentChatCache) -> None:
    """Persist the chat cache as a plain JSON file (matches existing CLI credential
    storage convention; see ``client/cli/v2/config_cmd.py``).
    """
    write_json_file(CHAT_CACHE_FILE, cache.model_dump_json(indent=2))


def load_chat_config() -> DeploymentChatConfig:
    """Load the chat config; return an empty config when the file is absent or unreadable."""
    raw = read_json_file(CHAT_CONFIG_FILE)
    if raw is None:
        return DeploymentChatConfig()
    try:
        return DeploymentChatConfig.model_validate(raw)
    except ValidationError:
        print(
            f"WARNING: {CHAT_CONFIG_FILE} is in an invalid format and was ignored. "
            "Re-register tokens with `./bai deployment chat-config set`.",
            file=sys.stderr,
        )
        return DeploymentChatConfig()


def save_chat_config(config: DeploymentChatConfig) -> None:
    """Persist the chat config as a plain JSON file (matches existing CLI credential
    storage convention; see ``client/cli/v2/config_cmd.py``).
    """
    write_json_file(CHAT_CONFIG_FILE, config.model_dump_json(indent=2))
