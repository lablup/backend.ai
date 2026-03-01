"""Template tree builder registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_template_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the template tree: cluster + session sub-registries."""
    from ai.backend.manager.api.rest.cluster_template.registry import (
        register_cluster_template_routes,
    )
    from ai.backend.manager.api.rest.session_template.registry import (
        register_session_template_routes,
    )

    reg = RouteRegistry.create("template", deps.cors_options)
    reg.add_subregistry(register_cluster_template_routes(deps))
    reg.add_subregistry(register_session_template_routes(deps))
    return reg
