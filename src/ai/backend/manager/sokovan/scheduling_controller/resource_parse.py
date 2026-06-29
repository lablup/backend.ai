"""Shared helpers for parsing resource quantity strings.

Both the preparer (``ComputeKernelResourcesRule``) and the validator
(``ResourceLimitRule``) need to coerce caller-supplied quantity strings
to :class:`Decimal`. Legacy enqueue paths pass BinarySize shortcuts
(``"512m"``, ``"1g"``) alongside plain decimal strings, so the coercion
must tolerate both forms — otherwise ``Decimal("512m")`` raises and
kills the whole request.

Keeping this in a dedicated module avoids cross-importing rules
between the preparer and validator packages.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from ai.backend.common.types import BinarySize
from ai.backend.manager.data.session.creation import ImageInfo


def parse_quantity(raw: Any) -> Decimal:
    """Best-effort parse of a resource quantity into :class:`Decimal`.

    Accepts both plain decimal strings (``"1"``, ``"1.5"``) and
    BinarySize-style shortcuts (``"512m"``, ``"1g"``).
    """
    if isinstance(raw, Decimal):
        return raw
    try:
        return Decimal(int(BinarySize.from_str(str(raw))))
    except (ValueError, TypeError):
        return Decimal(str(raw))


def image_min_slots(image_info: ImageInfo) -> dict[str, Decimal]:
    """Project ``ImageInfo.resource_spec`` into a ``{slot_name: min}`` map."""
    slots: dict[str, Decimal] = {}
    for slot_name, slot_spec in image_info.resource_spec.items():
        raw_min = slot_spec.get("min") if isinstance(slot_spec, Mapping) else None
        if raw_min is None:
            slots[slot_name] = Decimal(0)
            continue
        slots[slot_name] = parse_quantity(raw_min)
    return slots


__all__ = ("image_min_slots", "parse_quantity")
