# Kept for backward-compatibility of the plugins relying on the old common.logging module.
import warnings

from ai.backend.logging import BraceStyleAdapter

__all__ = ("BraceStyleAdapter",)

warnings.warn(
    "Please import BraceStyleAdapter from ai.backend.logging instead of ai.backend.common.logging",
    DeprecationWarning,
)
