"""Request DTOs for OpenAI-compatible inference endpoints (vLLM, SGLang, NIM, TGI)."""

from __future__ import annotations

from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema


class ChatCompletionMessage(BackendAISchema):
    """One message inside a chat-completions request."""

    role: str
    content: str


class ChatCompletionRequest(BackendAISchema):
    """Body for ``POST /v1/chat/completions`` (OpenAI-compatible).

    Extra fields are forwarded so callers can pass runtime-variant-specific
    knobs (e.g. ``temperature``, ``top_p``, vLLM/NIM extensions) through
    ``./bai deployment chat --params`` without the CLI having to enumerate
    them.
    """

    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[ChatCompletionMessage]
