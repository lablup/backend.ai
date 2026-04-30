"""``./bai deployment chat`` and ``chat-config`` CLI commands.

Submodules:
- :mod:`commands` — Click command/group definitions.
- :mod:`types` — Pydantic models for the on-disk cache and config,
  including the ``.load()``/``.save()`` classmethods that wire them to
  ``~/.backend.ai/deployment_chat/*.json``.
- :mod:`utils` — file paths and shared JSON I/O helpers.
- :mod:`formatter` — display helpers (``mask_token``, ``DeploymentChatFormatter``).

OpenAI-compat wire DTOs live in :mod:`ai.backend.common.dto.clients.openai_compat`
so they can be reused by any backend.ai component.
"""

from .commands import chat, chat_config

__all__ = ("chat", "chat_config")
