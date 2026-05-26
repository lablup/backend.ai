"""Response DTOs for OpenAI-compatible inference endpoints (vLLM, SGLang, NIM, TGI)."""

from __future__ import annotations

from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema


class _OpenAICompatModel(BackendAISchema):
    """Base for OpenAI-compat response DTOs.

    Runtimes (vLLM, SGLang, NIM, TGI) ship runtime-specific extras
    (``usage``, ``system_fingerprint``, ``tool_calls``,
    ``reasoning_content``, ``prompt_logprobs``, ``owned_by``, ...).
    ``extra="allow"`` keeps them on the model so ``model_dump_json``
    round-trips faithfully back to the CLI's stdout pretty-print.
    """

    model_config = ConfigDict(extra="allow")


class ModelEntry(_OpenAICompatModel):
    """One entry in an OpenAI-compat ``GET /v1/models`` response."""

    id: str
    object: str = "model"


class ListModelsResponse(_OpenAICompatModel):
    """Body of ``GET /v1/models`` on an OpenAI-compat endpoint."""

    object: str = "list"
    data: list[ModelEntry]


class ChatCompletionResponseMessage(_OpenAICompatModel):
    """The ``message`` payload inside one OpenAI-compat choice.

    Only ``content`` is consumed by the CLI (for chat-history persistence);
    runtime-specific fields like ``tool_calls`` or ``reasoning_content``
    (DeepSeek-R1, Qwen-QwQ) pass through to the JSON pretty-printed output
    via the inherited ``extra="allow"``.
    """

    role: str | None = None
    content: str | None = None


class ChatCompletionResponseChoice(_OpenAICompatModel):
    """One entry in ``choices[]`` on a non-streaming chat-completion response.

    Streaming responses use ``delta`` instead of ``message``; this model
    intentionally requires ``message`` so a streaming chunk that slips
    through (the SDK never sets ``stream=true`` itself) fails loudly via
    ``ValidationError`` rather than corrupting persisted history.
    """

    message: ChatCompletionResponseMessage


class ChatCompletionResponse(_OpenAICompatModel):
    """Body of ``POST /v1/chat/completions`` (OpenAI-compatible).

    Only the path used by chat-history bookkeeping
    (``choices[0].message.content``) is typed here. Top-level extras
    (``id``, ``object``, ``created``, ``model``, ``usage``,
    ``system_fingerprint``, runtime-specific fields) ride through via
    the inherited ``extra="allow"`` so they survive the round-trip back
    to the user's stdout when the CLI pretty-prints the response.
    """

    choices: list[ChatCompletionResponseChoice]

    @property
    def assistant_message(self) -> str | None:
        """Text emitted by the model in the first choice, if any.

        Returns ``None`` when the response advertised no choices or when
        the assistant emitted only a tool-call (``message.content`` is
        ``null`` in that case). The CLI uses this to gate chat-history
        persistence: a half-recorded round (user logged but assistant
        missing) would skew future context, so we skip the save in that
        case.
        """
        if not self.choices:
            return None
        return self.choices[0].message.content
