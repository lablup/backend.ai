"""``./bai deployment chat`` and ``chat-config`` CLI commands.

Submodules:
- :mod:`commands` — Click command/group definitions.
- :mod:`storage` — disk load/save for chat cache & config.
- :mod:`utils` — file paths and shared JSON I/O helpers.
- :mod:`formatter` — display helpers (``mask_token``, ``DeploymentChatFormatter``).

Pure data types and DTOs live in :mod:`ai.backend.common.data.deployment_chat`
and :mod:`ai.backend.common.dto.clients.openai_compat` respectively, so they
can be reused by any backend.ai component.
"""

from .commands import chat, chat_config

__all__ = ("chat", "chat_config")
