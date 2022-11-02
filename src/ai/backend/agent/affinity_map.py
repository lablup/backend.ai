from __future__ import annotations

import enum
from collections import defaultdict
from typing import TYPE_CHECKING, Optional, Sequence

import attr
import networkx as nx

from ai.backend.common.types import DeviceName

if TYPE_CHECKING:
    from .resources import AbstractComputeDevice


class AffinityPolicy(enum.Enum):
    PREFER_SINGLE_NODE = 0
    INTERLEAVED = 1


@attr.define()
class AffinityHint:
    devices: Optional[Sequence[AbstractComputeDevice]]
    affinity_map: AffinityMap
    policy: AffinityPolicy


class AffinityMap(nx.Graph):
    """
    Represents the NUMA distance matrix of all device pairs from all compute device plugins.
    """

    def __init__(self) -> None:
        self.max_weight = 0
        super().__init__()

    def get_largest_device_cluster_with_lowest_distance_from_src_device(
        self,
        device_name: DeviceName,
        src_device: AbstractComputeDevice,
    ) -> Sequence[AbstractComputeDevice]:
        distance_sets: dict[int, nx.Graph] = defaultdict(nx.Graph)
        for v in self.neighbors(src_device):
            if v.device_name == device_name:
                weight = self.edges[src_device, v]["weight"]
                distance_sets[weight].add_edge(src_device, v, weight=weight)
        device_cluster_list = []
        for distance, device_set in distance_sets.items():
            components = nx.connected_components(device_set)
            for component in components:
                device_cluster_list.append((distance, component))
        # sort by: low distance first, large component first
        device_cluster_list.sort(key=lambda item: (item[0], -len(item[1])))
        largest_component: list[AbstractComputeDevice] = []
        for distance, device_set in device_cluster_list[:1]:
            for device in device_set:
                if device == src_device:
                    continue
                largest_component.append(device)
        return largest_component

    def get_device_clusters_with_lowest_distance(
        self,
        device_name: DeviceName,
    ) -> Sequence[Sequence[AbstractComputeDevice]]:
        device_cluster_list = []
        # FIXME: this is the intended logic but causes infinite loop.
        # for weight in range(self.max_weight + 1):
        for weight in [0]:
            subgraph = nx.subgraph_view(
                self,
                filter_node=lambda u: u.device_name == device_name,
                filter_edge=lambda u, v: self.edges[u, v]["weight"] == weight,
            )
            components = nx.connected_components(subgraph)
            for component in components:
                device_cluster_list.append((weight, component))
        # sort by: low distance first, large component first
        device_cluster_list.sort(key=lambda item: (item[0], -len(item[1])))
        return [device_set for distance, device_set in device_cluster_list]

    def get_distance_ordered_neighbors(
        self,
        src_devices: Optional[Sequence[AbstractComputeDevice]],
        device_name: DeviceName,
    ) -> Sequence[Sequence[AbstractComputeDevice]]:
        """
        Get the list of neighbor device clusters and their distance from the given source_devices
        with the same name.

        Example:
            Given a 4-core dual socket system:

            If the prior allocator has assigned (gpu0@node0, gpu1@node1),
            it will return (cpu0-3@node0, cpu4-7@node1).

            If the prior allocator has assigned (gpu0@node0, gpu1@node0),
            it will return (cpu0-3@node0) only.

        If source_devices is None, it will return the first largest connected component from the
        device distance matrix sharing the lowest distance values.
        """
        if src_devices is not None:
            neighbor_components = []
            zero_distance_components = nx.subgraph_view(
                self,
                filter_node=lambda u: u in src_devices,
                filter_edge=lambda u, v: self.edges[u, v]["weight"] == 0,
            )
            for src_device_component in nx.connected_components(zero_distance_components):
                # take the first device in this neighbor group
                src_device = next(iter(src_device_component))
                largest_component = (
                    self.get_largest_device_cluster_with_lowest_distance_from_src_device(
                        device_name,
                        src_device,
                    )
                )
                neighbor_components.append(largest_component)
            return neighbor_components
        else:
            components = self.get_device_clusters_with_lowest_distance(device_name)
            return components

    @classmethod
    def build(cls, devices: Sequence[AbstractComputeDevice]) -> AffinityMap:
        # TODO: allow compute plugins to customize distance calculation
        g = cls()
        max_weight = 0
        devices_copy = list(devices)
        while devices_copy:
            device1 = devices_copy.pop(0)
            g.add_edge(device1, device1, weight=0)
            for device2 in devices_copy:
                weight = abs((max(0, device2.numa_node or 0)) - max(0, (device1.numa_node or 0)))
                if max_weight < weight:
                    max_weight = weight
                g.add_edge(device1, device2, weight=weight)
        g.max_weight = max_weight
        return g
