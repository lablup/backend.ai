"""Response DTOs for OpenAI-compatible inference endpoints (vLLM, SGLang, NIM, TGI)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ModelEntry(BaseModel):
    """One entry in an OpenAI-compat ``GET /v1/models`` response.

    Runtimes (vLLM, SGLang, NIM) typically include extra fields such as
    ``created`` or ``owned_by``; ``extra="allow"`` keeps them on the
    model so future additions don't break parsing.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "model"


class ListModelsResponse(BaseModel):
    """Body of ``GET /v1/models`` on an OpenAI-compat endpoint."""

    model_config = ConfigDict(extra="allow")

    object: str = "list"
    data: list[ModelEntry]


class ChatCompletionResponseMessage(BaseModel):
    """The ``message`` payload inside one OpenAI-compat choice.

    Only ``content`` is consumed by the CLI (for chat-history persistence);
    ``extra="allow"`` keeps runtime-specific fields like ``tool_calls`` or
    ``reasoning_content`` (DeepSeek-R1, Qwen-QwQ) on the model so they pass
    through to the JSON pretty-printed output.
    """

    model_config = ConfigDict(extra="allow")

    role: str | None = None
    content: str | None = None


class ChatCompletionResponseChoice(BaseModel):
    """One entry in ``choices[]`` on a non-streaming chat-completion response.

    Streaming responses use ``delta`` instead of ``message``; this model
    intentionally requires ``message`` so a streaming chunk that slips
    through (the SDK never sets ``stream=true`` itself) fails loudly via
    ``ValidationError`` rather than corrupting persisted history.
    """

    model_config = ConfigDict(extra="allow")

    message: ChatCompletionResponseMessage


class ChatCompletionResponse(BaseModel):
    """Body of ``POST /v1/chat/completions`` (OpenAI-compatible).

    Only the path used by chat-history bookkeeping
    (``choices[0].message.content``) is typed here. The remaining
    top-level fields (``id``, ``object``, ``created``, ``model``,
    ``usage``, ``system_fingerprint``, runtime-specific extras) ride
    through via ``extra="allow"`` so they survive the round-trip back
    to the user's stdout when the CLI pretty-prints the response.
    """

    model_config = ConfigDict(extra="allow")

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
