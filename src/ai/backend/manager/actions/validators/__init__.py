from dataclasses import dataclass

from .rbac import LegacyRBACValidators, RBACValidators


@dataclass
class ActionValidators:
    rbac: RBACValidators
    legacy_rbac: LegacyRBACValidators
