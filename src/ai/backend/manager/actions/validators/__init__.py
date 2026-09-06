from dataclasses import dataclass

from .rbac import LegacyRBACValidators, RBACValidators, VirtualEntityRBACValidators


@dataclass
class ActionValidators:
    rbac: RBACValidators
    virtual_entity_rbac: VirtualEntityRBACValidators
    # Optional so existing test fixtures that only pass `rbac=` keep working.
    # Production code (composer) always sets both; processors that need the
    # legacy validator fall back to `rbac` when this is None.
    legacy_rbac: LegacyRBACValidators | None = None
