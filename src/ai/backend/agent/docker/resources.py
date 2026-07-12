"""Compatibility surface for the compute-plugin API.

The implementations moved to ``ai.backend.agent.resources``: none of them is Docker-specific, and
keeping them here forced the containerd backend to import from the Docker backend.

Nothing in-tree depends on this module any more: the accelerator plugins already preferred
``ai.backend.agent.resources`` and only fell back here on ImportError, so that fallback is now
dead. It is kept solely so out-of-tree plugins pinned to the old path keep importing. Import from
``ai.backend.agent.resources`` in new code.
"""

from ai.backend.agent.resources import (
    get_resource_spec_from_container,
    load_resources,
    scan_available_resources,
)

__all__ = (
    "get_resource_spec_from_container",
    "load_resources",
    "scan_available_resources",
)
