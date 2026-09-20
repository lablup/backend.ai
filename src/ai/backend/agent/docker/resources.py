"""The compute-plugin loaders, importable under their Docker-era name.

They live in ``ai.backend.agent.resources`` (they are runtime-neutral); the accelerator plugins and
the Docker discovery still name this module.
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
