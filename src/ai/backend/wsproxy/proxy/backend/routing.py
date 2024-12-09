from ...config import RouteConfig
from .abc import AbstractRouteSelector


def create_route_selector(config: RouteConfig) -> AbstractRouteSelector:
    pass


class WeightedRoundRobinRouteSelector(AbstractRouteSelector):
    pass


class UniformRandomRouteSelector(AbstractRouteSelector):
    pass
