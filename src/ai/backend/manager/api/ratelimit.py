"""Backward-compatibility shim for the ratelimit module.

The rate-limit middleware logic has been migrated to:

* ``api.rest.ratelimit.handler`` — ``rlim_middleware``
* ``api.rest.ratelimit.registry`` — lifecycle management

The ``PrivateContext`` and lifecycle hooks (``init``/``shutdown``) have
been removed from this module as part of the DependencyComposer migration.
They now live in ``api.rest.ratelimit.registry``.

Re-exports are kept here for backward compatibility with existing imports.
"""

from __future__ import annotations

from ai.backend.manager.api.rest.ratelimit.handler import _rlim_window, rlim_middleware
from ai.backend.manager.api.rest.ratelimit.registry import RatelimitContext

__all__ = (
    "RatelimitContext",
    "_rlim_window",
    "rlim_middleware",
)
