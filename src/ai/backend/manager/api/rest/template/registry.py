"""Template tree builder registrar."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_template_routes(
    route_deps: RouteDeps,
    sub_registries: Sequence[RouteRegistry],
) -> RouteRegistry:
    """Build the template tree: cluster + session sub-registries."""
    reg = RouteRegistry.create("template", route_deps.cors_options)
    for sub in sub_registries:
        reg.add_subregistry(sub)
    return reg
