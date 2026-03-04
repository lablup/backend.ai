from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class DeploymentPolicyModifier(PartialModifier):
    """Modifier for partial updates to a deployment policy.

    Uses OptionalState to support partial updates — only fields
    explicitly set via OptionalState.update() will be applied.
    """

    strategy: OptionalState[DeploymentStrategy] = field(
        default_factory=OptionalState[DeploymentStrategy].nop
    )
    strategy_spec: OptionalState[RollingUpdateSpec | BlueGreenSpec] = field(
        default_factory=OptionalState[RollingUpdateSpec | BlueGreenSpec].nop
    )
    rollback_on_failure: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.strategy.update_dict(to_update, "strategy")
        self.strategy_spec.update_dict(to_update, "strategy_spec")
        self.rollback_on_failure.update_dict(to_update, "rollback_on_failure")
        return to_update
