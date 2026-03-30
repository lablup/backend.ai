from .base import (
    BaseAction,
    BaseActionResult,
    BaseActionResultMeta,
    BaseActionTriggerMeta,
    ProcessResult,
    SearchActionResult,
    TAction,
    TActionResult,
)
from .batch import (
    BaseBatchAction,
    BaseBatchActionResult,
)
from .rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
    build_operation_description,
)
from .rbac_model_deployment import (
    ModelDeploymentCreateRBACAction,
    ModelDeploymentGetRBACAction,
    ModelDeploymentHardDeleteRBACAction,
    ModelDeploymentSearchRBACAction,
    ModelDeploymentUpdateRBACAction,
)
from .rbac_session import (
    SessionCreateRBACAction,
    SessionGetRBACAction,
    SessionGrantAllRBACAction,
    SessionGrantHardDeleteRBACAction,
    SessionGrantReadRBACAction,
    SessionGrantUpdateRBACAction,
    SessionHardDeleteRBACAction,
    SessionSearchRBACAction,
    SessionUpdateRBACAction,
)

RBAC_ACTION_REGISTRY: tuple[type[BaseRBACAction], ...] = (
    ModelDeploymentCreateRBACAction,
    ModelDeploymentGetRBACAction,
    ModelDeploymentSearchRBACAction,
    ModelDeploymentUpdateRBACAction,
    ModelDeploymentHardDeleteRBACAction,
    SessionCreateRBACAction,
    SessionGetRBACAction,
    SessionSearchRBACAction,
    SessionUpdateRBACAction,
    SessionHardDeleteRBACAction,
    SessionGrantAllRBACAction,
    SessionGrantReadRBACAction,
    SessionGrantUpdateRBACAction,
    SessionGrantHardDeleteRBACAction,
)

__all__ = (
    "BaseAction",
    "BaseActionResult",
    "BaseActionResultMeta",
    "BaseActionTriggerMeta",
    "BaseBatchAction",
    "BaseBatchActionResult",
    "BaseRBACAction",
    "RBACActionName",
    "RBACRequiredPermission",
    "build_operation_description",
    "RBAC_ACTION_REGISTRY",
    "ProcessResult",
    "SearchActionResult",
    "TAction",
    "TActionResult",
)
