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
