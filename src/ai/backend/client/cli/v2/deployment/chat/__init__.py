"""``./bai deployment chat``, ``chat-config``, ``chat-cache``, and ``chat-history`` CLI commands.

Submodules:
- :mod:`commands` — Click command/group definitions.
- :mod:`types` — Pydantic models for the on-disk cache, config, and history,
  including the ``.load()``/``.save()`` classmethods that wire them to
  ``~/.backend.ai/deployment_chat/*.json``.
- :mod:`utils` — file paths and shared JSON I/O helpers.
- :mod:`formatter` — display helpers (``mask_token``, ``DeploymentChatFormatter``).

OpenAI-compat wire DTOs live in :mod:`ai.backend.common.dto.clients.openai_compat`
so they can be reused by any backend.ai component.
"""

from .commands import chat, chat_cache, chat_config, chat_history

__all__ = ("chat", "chat_cache", "chat_config", "chat_history")
