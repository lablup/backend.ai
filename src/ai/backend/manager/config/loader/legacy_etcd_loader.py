import urllib
from collections.abc import Mapping
from contextvars import ContextVar
from typing import Any, Optional, Sequence, TypeAlias, override

import aiotools
import yarl

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.identity import get_instance_id
from ai.backend.common.types import SlotName, SlotTypes, current_resource_slots
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.config.loader.types import AbstractConfigLoader
from ai.backend.manager.defs import INTRINSIC_SLOTS
from ai.backend.manager.errors.common import ServerMisconfiguredError

current_vfolder_types: ContextVar[list[str]] = ContextVar("current_vfolder_types")


NestedStrKeyedDict: TypeAlias = "dict[str, Any | NestedStrKeyedDict]"


class LegacyEtcdLoader(AbstractConfigLoader):
    _etcd: AsyncEtcd
    _config_prefix: str = "config"

    def __init__(self, etcd: AsyncEtcd, config_prefix: Optional[str] = None) -> None:
        super().__init__()
        self._etcd = etcd
        if config_prefix:
            self._config_prefix = config_prefix

    @override
    async def load(self) -> Mapping[str, Any]:
        raw_cfg = await self._etcd.get_prefix(self._config_prefix)
        return raw_cfg

    async def close(self) -> None:
        await self._etcd.close()

    def __hash__(self) -> int:
        # When used as a key in dicts, we don't care our contents.
        # Just treat it like an opaque object.
        return hash(id(self))

    @classmethod
    def flatten(cls, key_prefix: str, inner_dict: NestedStrKeyedDict) -> dict[str, str]:
        flattened_dict: dict[str, str] = {}
        for k, v in inner_dict.items():
            if k == "":
                flattened_key = key_prefix
            else:
                flattened_key = key_prefix + "/" + urllib.parse.quote(k, safe="")
            match v:
                case Mapping():
                    flattened_dict.update(cls.flatten(flattened_key, v))  # type: ignore
                case str():
                    flattened_dict[flattened_key] = v
                case int() | float() | yarl.URL():
                    flattened_dict[flattened_key] = str(v)
                case _:
                    raise ValueError(
                        f"The value {v!r} must be serialized before storing to the etcd"
                    )
        return flattened_dict

    async def get_raw(self, key: str, allow_null: bool = True) -> Optional[str]:
        value = await self._etcd.get(key)
        if not allow_null and value is None:
            raise ServerMisconfiguredError("A required etcd config is missing.", key)
        return value

    async def register_myself(self) -> None:
        instance_id = await get_instance_id()
        manager_info = {
            f"nodes/manager/{instance_id}": "up",
        }
        await self._etcd.put_dict(manager_info)

    async def deregister_myself(self) -> None:
        instance_id = await get_instance_id()
        await self._etcd.delete_prefix(f"nodes/manager/{instance_id}")

    async def update_resource_slots(
        self,
        slot_key_and_units: Mapping[SlotName, SlotTypes],
    ) -> None:
        updates = {}
        known_slots = await self.get_resource_slots()
        for k, v in slot_key_and_units.items():
            if k not in known_slots or v != known_slots[k]:
                updates[f"config/resource_slots/{k}"] = v.value
        if updates:
            await self._etcd.put_dict(updates)

    async def update_manager_status(self, status) -> None:
        await self._etcd.put("manager/status", status.value)
        self.get_manager_status.cache_clear()

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def _get_resource_slots(self):
        raw_data = await self._etcd.get_prefix_dict("config/resource_slots")
        return {SlotName(k): SlotTypes(v) for k, v in raw_data.items()}

    async def get_resource_slots(self) -> Mapping[SlotName, SlotTypes]:
        """
        Returns the system-wide known resource slots and their units.
        """
        try:
            ret = current_resource_slots.get()
        except LookupError:
            configured_slots = await self._get_resource_slots()
            ret = {**INTRINSIC_SLOTS, **configured_slots}
            current_resource_slots.set(ret)
        return ret

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def _get_vfolder_types(self):
        return await self._etcd.get_prefix("volumes/_types")

    async def get_vfolder_types(self) -> Sequence[str]:
        """
        Returns the vfolder types currently set. One of "user" and/or "group".
        If none is specified, "user" type is implicitly assumed.
        """
        try:
            ret = current_vfolder_types.get()
        except LookupError:
            vf_types = await self._get_vfolder_types()
            ret = list(vf_types.keys())
            current_vfolder_types.set(ret)
        return ret

    @aiotools.lru_cache(maxsize=1, expire_after=5.0)
    async def get_manager_nodes_info(self):
        return await self._etcd.get_prefix_dict("nodes/manager")

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def get_manager_status(self) -> ManagerStatus:
        status = await self._etcd.get("manager/status")
        if status is None:
            return ManagerStatus.TERMINATED
        return ManagerStatus(status)

    async def watch_manager_status(self):
        async with aiotools.aclosing(self._etcd.watch("manager/status")) as agen:
            async for ev in agen:
                yield ev

    # TODO: refactor using contextvars in Python 3.7 so that the result is cached
    #       in a per-request basis.
    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def get_allowed_origins(self):
        return await self._etcd.get("config/api/allow-origins")


class LegacyEtcdVolumesLoader(AbstractConfigLoader):
    _etcd: AsyncEtcd
    _config_prefix: str = "volumes"

    def __init__(self, etcd: AsyncEtcd) -> None:
        super().__init__()
        self._etcd = etcd

    @override
    async def load(self) -> Mapping[str, Any]:
        raw_cfg = await self._etcd.get_prefix(self._config_prefix)
        return {"volumes": raw_cfg}
