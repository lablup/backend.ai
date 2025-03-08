from ...config import RoutingConfig
from .abc import AbstractRouteSelector


def create_route_selector(config: RoutingConfig) -> AbstractRouteSelector:
    raise NotImplementedError


class WeightedRoundRobinRouteSelector(AbstractRouteSelector):
    pass


class UniformRandomRouteSelector(AbstractRouteSelector):
    pass
