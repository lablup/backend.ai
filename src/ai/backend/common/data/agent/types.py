from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Final

from pydantic import Field, field_validator

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.types import (
    BackendAISchema,
    DeviceName,
    ResourceSlotEntry,
    SlotName,
    SlotTypes,
)

MAX_NODE_SHAPES: Final = 256
"""The most distinct node shapes a heartbeat carries."""


class AgentInfo(BackendAISchema):
    ip: str
    region: str | None
    scaling_group: str | None
    addr: str
    public_key: PublicKey | None
    public_host: str
    available_resource_slots: list[ResourceSlotEntry]
    slot_key_and_units: dict[ResourceSlotName, SlotTypes]
    version: str
    compute_plugins: dict[DeviceName, dict[str, Any]]
    architecture: str
    auto_terminate_abusing_kernel: bool
    node_shapes: list[dict[str, str]] | None = Field(
        default=None,
        description=(
            "The distinct allocatable shapes (slot name to decimal string) of the nodes a"
            " compute cluster's gateway counts; None for an agent that is not a gateway."
            f" Added in {NEXT_RELEASE_VERSION}."
        ),
    )

    @field_validator("slot_key_and_units", mode="before")
    @classmethod
    def normalize_slot_keys(
        cls, value: dict[str | SlotName, SlotTypes]
    ) -> dict[ResourceSlotName, SlotTypes]:
        """Accept `SlotName` keys from older agent versions, which sent the legacy form."""
        if not isinstance(value, dict):
            raise ValueError("slot_key_and_units must be a dictionary")
        return {ResourceSlotName(str(key)): val for key, val in value.items()}

    @field_validator("node_shapes", mode="after")
    @classmethod
    def normalize_node_shapes(
        cls, value: list[dict[str, str]] | None
    ) -> list[dict[str, str]] | None:
        """Keep the first `MAX_NODE_SHAPES` distinct shapes whose quantities are finite
        non-negative decimals, so one bad node never drops the heartbeat."""
        if value is None:
            return None
        seen: set[tuple[tuple[str, str], ...]] = set()
        shapes: list[dict[str, str]] = []
        for shape in value:
            if not _is_valid_shape(shape):
                continue
            key = tuple(sorted(shape.items()))
            if key in seen:
                continue
            seen.add(key)
            shapes.append(shape)
            if len(shapes) == MAX_NODE_SHAPES:
                break
        return shapes


def _is_valid_shape(shape: dict[str, str]) -> bool:
    for quantity in shape.values():
        try:
            parsed = Decimal(quantity)
        except InvalidOperation:
            return False
        if not parsed.is_finite() or parsed < 0:
            return False
    return bool(shape)
