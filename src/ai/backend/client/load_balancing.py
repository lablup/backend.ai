from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import List, Mapping, Tuple, Type

import attr
from yarl import URL


@attr.s(auto_attribs=True, frozen=True)
class LoadBalancerConfig():
    name: str
    args: Tuple[str, ...]


class LoadBalancer(metaclass=ABCMeta):

    @staticmethod
    def load(config: LoadBalancerConfig) -> LoadBalancer:
        cls = _cls_map[config.name]
        return cls(*config.args)

    @staticmethod
    def clean_config(config: str) -> LoadBalancerConfig:
        name, _, raw_args = config.partition(':')
        args = raw_args.split(',')
        return LoadBalancerConfig(name, tuple(args))

    @abstractmethod
    def rotate(self, endpoints: List[URL]) -> None:
        raise NotImplementedError


class SimpleRRLoadBalancer(LoadBalancer):
    """
    Rotates the endpoints upon every request.
    """

    def rotate(self, endpoints: List[URL]) -> None:
        if len(endpoints) == 1:
            return
        item = endpoints.pop(0)
        endpoints.append(item)


class PeriodicRRLoadBalancer(LoadBalancer):
    """
    Rotates the endpoints upon the specified interval.
    """

    def rotate(self, endpoints: List[URL]) -> None:
        pass


class LowestLatencyLoadBalancer(LoadBalancer):
    """
    Change the endpoints with the lowest average latency for last N requests.
    """

    def rotate(self, endpoints: List[URL]) -> None:
        pass

    # TODO: we need to collect and allow access to the latency statistics.


_cls_map: Mapping[str, Type[LoadBalancer]] = {
    'simple_rr': SimpleRRLoadBalancer,
    'periodic_rr': PeriodicRRLoadBalancer,
    'lowest_latency': LowestLatencyLoadBalancer,
}
