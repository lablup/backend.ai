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
    """
    Represents the distance matrix of all device pairs from all compute device plugins.
    """

    def get_largest_device_cluster_with_lowest_distance_from_src_device(
        self,
        device_name: DeviceName,
        src_device: AbstractComputeDevice,
    ) -> Sequence[tuple[AbstractComputeDevice, int]]:
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
        largest_component: list[tuple[AbstractComputeDevice, int]] = []
        for distance, device_set in device_cluster_list[:1]:
            for device in device_set:
                if device == src_device:
                    continue
                largest_component.append((device, distance))
        return largest_component

    def get_largest_device_cluster_with_lowest_distance(
        self,
        device_name: DeviceName,
    ) -> Sequence[tuple[AbstractComputeDevice, int]]:
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
        # sort by: low distance first, large component first
        device_cluster_list.sort(key=lambda item: (item[0], -len(item[1])))
        largest_component: list[tuple[AbstractComputeDevice, int]] = []
        for distance, device_set in device_cluster_list[:1]:
            for device in device_set:
                largest_component.append((device, distance))
        return largest_component

    def get_distance_ordered_neighbors(
        self,
        src_devices: Optional[Sequence[AbstractComputeDevice]],
        device_name: DeviceName,
    ) -> Sequence[Sequence[tuple[AbstractComputeDevice, int]]]:
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
            # print("src_devices:", ",".join(d.device_id for d in src_devices))
            zero_distance_components = nx.subgraph_view(
                self,
                filter_node=lambda v: v in src_devices,
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
            # print(
            #     "neighbor_components:",
            #     ", ".join(
            #         "{" + ",".join(d.device_id for d, distance in c) + "}"
            #         for c in neighbor_components
            #     ),
            # )
            return neighbor_components
        else:
            # TODO: implement the interleaving policy
            #   - If we do interleaved allocation for the first device type,
            #     all subsequent alloactions for other device types will automatically
            #     do interleaving because we use neighbor groups.
            largest_component = self.get_largest_device_cluster_with_lowest_distance(device_name)
            return [largest_component]

    @classmethod
    def build(cls, devices: Sequence[AbstractComputeDevice]) -> AffinityMap:
        # TODO: allow compute plugins to customize distance calculation
        g = cls()
        for device1 in devices:
            for device2 in devices:
                g.add_edge(
                    device1,
                    device2,
                    weight=abs((device2.numa_node or 0) - (device1.numa_node or 0)),
                )
        return g
