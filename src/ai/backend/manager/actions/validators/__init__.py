from dataclasses import dataclass

from .rbac import RBACValidators


@dataclass
class ActionValidators:
    rbac: RBACValidators
