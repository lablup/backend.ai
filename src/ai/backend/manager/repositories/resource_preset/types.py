"""Type definitions for resource preset repository."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.json import dump_json, load_json
from ai.backend.common.types import SlotQuantity
from ai.backend.manager.repositories.resource_slot.types import (
    quantities_from_json,
    quantities_to_json,
)

from .db_source.types import PerScalingGroupResourceData, PresetAllocatabilityData


@dataclass
class CheckPresetsResult:
    """Result of checking resource presets from repository."""

    presets: list[PresetAllocatabilityData]
    keypair_limits: list[SlotQuantity]
    keypair_using: list[SlotQuantity]
    keypair_remaining: list[SlotQuantity]
    group_limits: list[SlotQuantity]
    group_using: list[SlotQuantity]
    group_remaining: list[SlotQuantity]
    scaling_group_remaining: list[SlotQuantity]
    scaling_groups: dict[str, PerScalingGroupResourceData]

    def to_cache(self) -> bytes:
        """
        Serialize the result to a JSON string for caching.

        :return: JSON bytes representation of the result
        """
        cache_data = {
            "presets": [p.to_cache() for p in self.presets],
            "keypair_limits": quantities_to_json(self.keypair_limits),
            "keypair_using": quantities_to_json(self.keypair_using),
            "keypair_remaining": quantities_to_json(self.keypair_remaining),
            "group_limits": quantities_to_json(self.group_limits),
            "group_using": quantities_to_json(self.group_using),
            "group_remaining": quantities_to_json(self.group_remaining),
            "scaling_group_remaining": quantities_to_json(self.scaling_group_remaining),
            "scaling_groups": {
                sgname: sg_data.to_cache() for sgname, sg_data in self.scaling_groups.items()
            },
        }

        return dump_json(cache_data)

    @classmethod
    def from_cache(cls, cached_data: bytes) -> CheckPresetsResult:
        """
        Deserialize the result from a cached JSON string.

        :param cached_data: JSON bytes from cache
        :return: CheckPresetsResult instance
        """
        data = load_json(cached_data)

        return cls(
            presets=[PresetAllocatabilityData.from_cache(p) for p in data["presets"]],
            keypair_limits=quantities_from_json(data["keypair_limits"]),
            keypair_using=quantities_from_json(data["keypair_using"]),
            keypair_remaining=quantities_from_json(data["keypair_remaining"]),
            group_limits=quantities_from_json(data["group_limits"]),
            group_using=quantities_from_json(data["group_using"]),
            group_remaining=quantities_from_json(data["group_remaining"]),
            scaling_group_remaining=quantities_from_json(data["scaling_group_remaining"]),
            scaling_groups={
                sgname: PerScalingGroupResourceData.from_cache(sg_data)
                for sgname, sg_data in data["scaling_groups"].items()
            },
        )
