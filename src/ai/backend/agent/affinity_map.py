from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Optional, Sequence

import attr
import networkx as nx

from ai.backend.common.types import DeviceName

if TYPE_CHECKING:
    from .resources import AbstractComputeDevice


@attr.define()
class AffinityHint:
    devices: Optional[Sequence[AbstractComputeDevice]]
    affinity_map: AffinityMap


class AffinityMap(nx.Graph):
    def get_distance_ordered_neighbors(
        self,
        src_device: Optional[AbstractComputeDevice],
        device_name: DeviceName,
    ) -> Sequence[tuple[AbstractComputeDevice, int]]:
        """
        Get the list of neighbor devices and their distance from the given source device with the same type.
        If the given sourec device is None, it will return the list of devices with the same type,
        but the first largest connected component from the devices sharing the lowest distance values.
        """
        if src_device is not None:
            neighbors = [
                device for device in self.neighbors(src_device) if device.device_name == device_name
            ]
            neighbors.sort(key=lambda device: self.edges[src_device, device]["weight"])
            return [(device, self.edges[src_device, device]["weight"]) for device in neighbors]
        else:
            distance_sets: dict[int, nx.Graph] = defaultdict(nx.Graph)
            subgraph = nx.subgraph_view(
                self,
                filter_node=lambda device: device.device_name == device_name,
            )
            for u, v, weight in subgraph.edges.data("weight"):
                distance_sets[weight].add_edge(u, v)
            device_cluster_list = []
            for distance, device_set in distance_sets.items():
                components = nx.connected_components(device_set)
                for component in components:
                    device_cluster_list.append((distance, component))
            device_cluster_list.sort(key=lambda item: (item[0], -len(item[1])))
            largest_component: list[tuple[AbstractComputeDevice, int]] = []
            for distance, device_set in device_cluster_list[:1]:
                for device in device_set:
                    largest_component.append((device, distance))
            return largest_component

    @classmethod
    def build(cls, devices: Sequence[AbstractComputeDevice]) -> AffinityMap:
        g = cls()
        for device1 in devices:
            for device2 in devices:
                g.add_edge(
                    device1,
                    device2,
                    weight=abs((device2.numa_node or 0) - (device1.numa_node or 0)),
                )
        return g
