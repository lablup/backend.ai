"""DTOs for OpenAI-compatible Chat Completions endpoints.

Wire-format Pydantic models for the OpenAI HTTP contract that vLLM, SGLang,
NVIDIA NIM, and TGI (in messages-api mode) implement. Kept under
``common/dto/clients/`` so any backend.ai component (CLI today, manager or
agent tomorrow) can consume the same types when talking to a deployed model.
"""

from .request import ChatCompletionMessage, ChatCompletionRequest
from .response import ListModelsResponse, ModelEntry

__all__ = (
    "ChatCompletionMessage",
    "ChatCompletionRequest",
    "ListModelsResponse",
    "ModelEntry",
)
