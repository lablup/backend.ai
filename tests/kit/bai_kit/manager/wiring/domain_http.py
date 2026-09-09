"""Domain routes for the HTTP runner. Kept apart from ``domain.py``: the route registry
imports the auth middleware, which drags the whole REST layer into the closure."""

from __future__ import annotations

from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.domain.handler import V2DomainHandler
from ai.backend.manager.api.rest.v2.domain.registry import register_v2_domain_routes


def domain_routes(adapter: DomainAdapter, route_deps: RouteDeps) -> RouteRegistry:
    return register_v2_domain_routes(V2DomainHandler(adapter=adapter), route_deps)
