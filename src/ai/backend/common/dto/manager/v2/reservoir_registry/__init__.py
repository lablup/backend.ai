"""Reservoir Registry DTOs v2 for Manager API."""

from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    AdminSearchReservoirRegistriesInput,
    CreateReservoirRegistryInput,
    DeleteReservoirRegistryInput,
    UpdateReservoirRegistryInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    AdminSearchReservoirRegistriesPayload,
    CreateReservoirRegistryPayload,
    DeleteReservoirRegistryPayload,
    ReservoirRegistryNode,
    UpdateReservoirRegistryPayload,
)

__all__ = (
    "AdminSearchReservoirRegistriesInput",
    "AdminSearchReservoirRegistriesPayload",
    "CreateReservoirRegistryInput",
    "CreateReservoirRegistryPayload",
    "DeleteReservoirRegistryInput",
    "DeleteReservoirRegistryPayload",
    "ReservoirRegistryNode",
    "UpdateReservoirRegistryInput",
    "UpdateReservoirRegistryPayload",
)
