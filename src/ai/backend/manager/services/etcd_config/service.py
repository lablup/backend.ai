from __future__ import annotations

import collections
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from ai.backend.common.json import load_json
from ai.backend.common.types import AcceleratorMetadata
from ai.backend.manager.errors.api import InvalidAPIParameters

from .actions.delete_config import DeleteConfigAction, DeleteConfigActionResult
from .actions.get_config import GetConfigAction, GetConfigActionResult
from .actions.get_resource_metadata import (
    GetResourceMetadataAction,
    GetResourceMetadataActionResult,
)
from .actions.get_resource_slots import GetResourceSlotsAction, GetResourceSlotsActionResult
from .actions.get_vfolder_types import GetVfolderTypesAction, GetVfolderTypesActionResult
from .actions.set_config import SetConfigAction, SetConfigActionResult

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.repositories.etcd_config import EtcdConfigRepository

__all__ = ("EtcdConfigService",)

KNOWN_SLOT_METADATA: dict[str, AcceleratorMetadata] = {
    "cpu": {
        "slot_name": "cpu",
        "description": "CPU",
        "human_readable_name": "CPU",
        "display_unit": "Core",
        "number_format": {"binary": False, "round_length": 0},
        "display_icon": "cpu",
    },
    "mem": {
        "slot_name": "ram",
        "description": "Memory",
        "human_readable_name": "RAM",
        "display_unit": "GiB",
        "number_format": {"binary": True, "round_length": 0},
        "display_icon": "cpu",
    },
    "cuda.device": {
        "slot_name": "cuda.device",
        "human_readable_name": "GPU",
        "description": "CUDA-capable GPU",
        "display_unit": "GPU",
        "number_format": {"binary": False, "round_length": 0},
        "display_icon": "gpu1",
    },
    "cuda.shares": {
        "slot_name": "cuda.shares",
        "human_readable_name": "fGPU",
        "description": "CUDA-capable GPU (fractional)",
        "display_unit": "fGPU",
        "number_format": {"binary": False, "round_length": 2},
        "display_icon": "gpu1",
    },
    "rocm.device": {
        "slot_name": "rocm.device",
        "human_readable_name": "GPU",
        "description": "ROCm-capable GPU",
        "display_unit": "GPU",
        "number_format": {"binary": False, "round_length": 0},
        "display_icon": "gpu2",
    },
    "tpu.device": {
        "slot_name": "tpu.device",
        "human_readable_name": "TPU",
        "description": "TPU device",
        "display_unit": "GPU",
        "number_format": {"binary": False, "round_length": 0},
        "display_icon": "tpu",
    },
}


@dataclass
class EtcdConfigService:
    """Service for etcd configuration operations."""

    _repository: EtcdConfigRepository
    _config_provider: ManagerConfigProvider
    _etcd: AsyncEtcd
    _valkey_stat: ValkeyStatClient

    def __init__(
        self,
        *,
        repository: EtcdConfigRepository,
        config_provider: ManagerConfigProvider,
        etcd: AsyncEtcd,
        valkey_stat: ValkeyStatClient,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider
        self._etcd = etcd
        self._valkey_stat = valkey_stat

    async def get_resource_slots(
        self, action: GetResourceSlotsAction
    ) -> GetResourceSlotsActionResult:
        """Get system-wide known resource slots."""
        known_slots = await self._config_provider.legacy_etcd_config_loader.get_resource_slots()
        return GetResourceSlotsActionResult(
            slots={str(k): v for k, v in known_slots.items()},
        )

    async def get_resource_metadata(
        self, action: GetResourceMetadataAction
    ) -> GetResourceMetadataActionResult:
        """Get resource metadata with optional scaling group filter."""
        known_slots = await self._config_provider.legacy_etcd_config_loader.get_resource_slots()

        # Collect plugin-reported accelerator metadata
        computer_metadata = await self._valkey_stat.get_computer_metadata()
        reported_accelerator_metadata: dict[str, AcceleratorMetadata] = {
            slot_name: cast(AcceleratorMetadata, load_json(metadata_json))
            for slot_name, metadata_json in computer_metadata.items()
        }

        # Merge reported metadata and preconfigured metadata (for legacy plugins)
        accelerator_metadata: dict[str, AcceleratorMetadata] = {}
        for slot_name, metadata in collections.ChainMap(
            reported_accelerator_metadata,
            KNOWN_SLOT_METADATA,
        ).items():
            if slot_name in known_slots:
                accelerator_metadata[slot_name] = metadata

        # Optionally filter by the slots reported by the given resource group's agents
        if action.sgroup is not None:
            available_slot_keys = await self._repository.get_available_agent_slots(action.sgroup)
            accelerator_metadata = {
                str(k): v
                for k, v in accelerator_metadata.items()
                if k in {"cpu", "mem", *available_slot_keys}
            }

        return GetResourceMetadataActionResult(metadata=accelerator_metadata)

    async def get_vfolder_types(self, action: GetVfolderTypesAction) -> GetVfolderTypesActionResult:
        """Get available vfolder types."""
        vfolder_types = await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        return GetVfolderTypesActionResult(types=list(vfolder_types))

    async def get_config(self, action: GetConfigAction) -> GetConfigActionResult:
        """Get raw etcd key-value."""
        if action.prefix:
            tree_value = dict(await self._etcd.get_prefix_dict(action.key))
            return GetConfigActionResult(result=tree_value)
        scalar_value = await self._etcd.get(action.key)
        return GetConfigActionResult(result=scalar_value)

    async def set_config(self, action: SetConfigAction) -> SetConfigActionResult:
        """Set raw etcd key-value."""
        if isinstance(action.value, Mapping):
            updates: dict[str, Any] = {}

            def flatten(prefix: str, o: Mapping[str, Any]) -> None:
                for k, v in o.items():
                    inner_prefix = prefix if k == "" else f"{prefix}/{k}"
                    if isinstance(v, Mapping):
                        flatten(inner_prefix, v)
                    else:
                        updates[inner_prefix] = v

            flatten(action.key, action.value)
            if len(updates) > 16:
                raise InvalidAPIParameters(
                    "Too large update! Split into smaller key-value pair sets."
                )
            await self._etcd.put_dict(updates)
        else:
            await self._etcd.put(action.key, action.value)
        return SetConfigActionResult()

    async def delete_config(self, action: DeleteConfigAction) -> DeleteConfigActionResult:
        """Delete raw etcd key-value."""
        if action.prefix:
            await self._etcd.delete_prefix(action.key)
        else:
            await self._etcd.delete(action.key)
        return DeleteConfigActionResult()
