import logging
from collections import defaultdict
from decimal import Decimal
from typing import DefaultDict, Iterable, List, Optional, Sequence, Set, Tuple

from ai.backend.agent.stats import (
    Measurement,
    MetricTypes,
    NodeMeasurement,
    StatContext,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceName,
    MetricKey,
    SlotName,
    SlotTypes,
)

from ..common.atom_api import ATOMAPI
from ..common.plugin import AbstractATOMPlugin
from .types import ATOMMaxChildDevice, ATOMMaxDevice

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

VALID_DEVICE_NAME = ("RBLN-CA25",)


class ATOMMaxPlugin(AbstractATOMPlugin[ATOMMaxDevice]):
    key = DeviceName("atom-max")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("atom-max.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"atom-max.device"}

    _all_devices: Optional[List[ATOMMaxDevice]]

    async def _list_devices(self) -> List[ATOMMaxDevice]:
        stats = await ATOMAPI.get_stats(self._rbln_stat_path)
        devices: List[ATOMMaxDevice] = []
        devices_by_sid: DefaultDict[DeviceId, List[ATOMMaxChildDevice]] = defaultdict(list)
        for device_info in stats.devices:
            if device_info.name not in VALID_DEVICE_NAME:
                continue
            assert device_info.sid is not None, (
                "sid value in atom-stats -j response cannot be null for ATOM Max device!"
            )
            devices_by_sid[DeviceId(device_info.sid)].append(
                ATOMMaxChildDevice(
                    serial=device_info.uuid,
                    hw_location=device_info.pci.bus_id,
                    device_number=device_info.npu,
                    rbln_stat_info=device_info,
                )
            )

        for sid, children in devices_by_sid.items():
            device_info = children[0].rbln_stat_info
            mother_device = ATOMMaxDevice(
                device_name=self.key,
                model_name=f"RBLN {device_info.name}",
                children=children,
                device_id=sid,
                hw_location=device_info.pci.bus_id,
                memory_size=int(device_info.memory.total) * len(children),
                processing_units=0,
                numa_node=device_info.pci.numa_node,
            )
            devices.append(mother_device)

        return devices

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        dev_count = 0
        mem_avail_total = 0
        mem_used_total = 0
        mem_stats: defaultdict[DeviceId, Measurement] = defaultdict(
            lambda: Measurement(Decimal(0), Decimal(0))
        )
        util_total = 0.0
        util_stats: defaultdict[DeviceId, Measurement] = defaultdict(
            lambda: Measurement(Decimal(0), Decimal(0))
        )

        stat_prefix = self.key.replace("-", "_")

        stats = await ATOMAPI.get_stats(self._rbln_stat_path)
        if self.enabled:
            for device in await self.list_devices():
                device_id = device.device_id
                for child in device.children:
                    pci_bus_id = child.hw_location
                    try:
                        stat = [x for x in stats.devices if x.pci.bus_id == pci_bus_id].pop()
                    except IndexError:
                        continue

                    mem_avail_total += int(stat.memory.total)
                    mem_used_total += int(stat.memory.used)
                    mem_stat = mem_stats[device_id]
                    mem_stat.value += Decimal(int(stat.memory.used))
                    if mem_stat.capacity:
                        mem_stat.capacity += Decimal(int(stat.memory.total))
                    util_total += float(stat.util)
                    util_stat = util_stats[device_id]
                    util_stat.value += Decimal(float(stat.util))
                    if util_stat.capacity:
                        util_stat.capacity += Decimal(100)
                    dev_count += 1
        return [
            NodeMeasurement(
                MetricKey(f"{stat_prefix}_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_total), Decimal(mem_avail_total)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey(f"{stat_prefix}_util"),
                MetricTypes.USAGE,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_node=Measurement(Decimal(util_total), Decimal(dev_count * 100)),
                per_device=util_stats,
            ),
        ]

    async def group_npus(
        self,
        devices: Iterable[ATOMMaxDevice],
    ) -> int:
        groups: Set[int] = set()
        device_indexes = []
        for d in devices:
            groups |= set([int(dd.rbln_stat_info.group_id) for dd in d.children])
        non_zero_groups: Set[int] = groups - set([0])
        if len(non_zero_groups) > 0:
            await ATOMAPI.destroy_groups(self._rbln_stat_path, list(non_zero_groups))

        # device index alters based on its group membership - so we need to query up to date device stat here
        unique_ids = {d.device_id for d in devices}
        live_devices = await self._list_devices()
        for d in live_devices:
            if d.device_id in unique_ids:
                device_indexes.extend([dd.rbln_stat_info.npu for dd in d.children])
        group_idx = await ATOMAPI.create_group(self._rbln_stat_path, device_indexes)
        return group_idx

    async def list_device_files(self, device: ATOMMaxDevice) -> Iterable[str]:
        return [f"/dev/{c.rbln_stat_info.device}" for c in device.children]

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "atom-max.device",
            "description": "ATOM Max",
            "human_readable_name": "ATOM Max Device",
            "display_unit": "ATOM Max",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "rebel",
        }
