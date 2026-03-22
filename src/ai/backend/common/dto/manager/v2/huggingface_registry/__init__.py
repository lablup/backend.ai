"""HuggingFace Registry DTOs v2 for Manager API."""

from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    AdminSearchHuggingFaceRegistriesInput,
    CreateHuggingFaceRegistryInput,
    DeleteHuggingFaceRegistryInput,
    UpdateHuggingFaceRegistryInput,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    AdminSearchHuggingFaceRegistriesPayload,
    CreateHuggingFaceRegistryPayload,
    DeleteHuggingFaceRegistryPayload,
    HuggingFaceRegistryNode,
    UpdateHuggingFaceRegistryPayload,
)

__all__ = (
    "AdminSearchHuggingFaceRegistriesInput",
    "AdminSearchHuggingFaceRegistriesPayload",
    "CreateHuggingFaceRegistryInput",
    "CreateHuggingFaceRegistryPayload",
    "DeleteHuggingFaceRegistryInput",
    "DeleteHuggingFaceRegistryPayload",
    "HuggingFaceRegistryNode",
    "UpdateHuggingFaceRegistryInput",
    "UpdateHuggingFaceRegistryPayload",
)
