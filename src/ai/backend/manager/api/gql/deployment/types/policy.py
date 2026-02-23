"""GraphQL types for DeploymentPolicy."""

from __future__ import annotations

from datetime import datetime
from typing import Self

import strawberry
from strawberry import ID
from strawberry.relay import Node, NodeID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.deployment.creator import DeploymentPolicyConfig
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.errors.deployment import InvalidDeploymentStrategySpec
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.repositories.deployment.updaters import DeploymentPolicyUpdaterSpec
from ai.backend.manager.types import OptionalState

# Enum defined here to avoid circular import with deployment.py
DeploymentStrategyTypeGQL: type[DeploymentStrategy] = strawberry.enum(
    DeploymentStrategy,
    name="DeploymentStrategyType",
    description="Added in 25.19.0. This enum represents the deployment strategy type of a model deployment, indicating the strategy used for deployment.",
)

# ========== Output Types (Response) ==========


@strawberry.interface(
    name="DeploymentStrategySpec",
    description="Added in 25.19.0. Base interface for deployment strategy specifications.",
)
class DeploymentStrategySpecGQL:
    strategy: DeploymentStrategyTypeGQL


@strawberry.type(
    name="RollingUpdateStrategySpec",
    description="Added in 25.19.0. Rolling update strategy specification.",
)
class RollingUpdateStrategySpecGQL(DeploymentStrategySpecGQL):
    max_surge: int
    max_unavailable: int


@strawberry.type(
    name="BlueGreenStrategySpec",
    description="Added in 25.19.0. Blue-green deployment strategy specification.",
)
class BlueGreenStrategySpecGQL(DeploymentStrategySpecGQL):
    auto_promote: bool
    promote_delay_seconds: int


@strawberry.type(
    name="DeploymentPolicy",
    description="Added in 25.19.0. Deployment policy configuration.",
)
class DeploymentPolicyGQL(Node):
    id: NodeID[str]
    strategy_spec: DeploymentStrategySpecGQL
    rollback_on_failure: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_data(cls, data: DeploymentPolicyData) -> Self:
        match data.strategy:
            case DeploymentStrategy.ROLLING:
                if not isinstance(data.strategy_spec, RollingUpdateSpec):
                    raise InvalidDeploymentStrategySpec(
                        "Expected RollingUpdateSpec for ROLLING strategy"
                    )
                return cls(
                    id=ID(str(data.id)),
                    strategy_spec=RollingUpdateStrategySpecGQL(
                        strategy=DeploymentStrategyTypeGQL.ROLLING,
                        max_surge=data.strategy_spec.max_surge,
                        max_unavailable=data.strategy_spec.max_unavailable,
                    ),
                    rollback_on_failure=data.rollback_on_failure,
                    created_at=data.created_at,
                    updated_at=data.updated_at,
                )
            case DeploymentStrategy.BLUE_GREEN:
                if not isinstance(data.strategy_spec, BlueGreenSpec):
                    raise InvalidDeploymentStrategySpec(
                        "Expected BlueGreenSpec for BLUE_GREEN strategy"
                    )
                return cls(
                    id=ID(str(data.id)),
                    strategy_spec=BlueGreenStrategySpecGQL(
                        strategy=DeploymentStrategyTypeGQL.BLUE_GREEN,
                        auto_promote=data.strategy_spec.auto_promote,
                        promote_delay_seconds=data.strategy_spec.promote_delay_seconds,
                    ),
                    rollback_on_failure=data.rollback_on_failure,
                    created_at=data.created_at,
                    updated_at=data.updated_at,
                )


# ========== Input Types ==========


@strawberry.input(
    name="RollingUpdateConfigInput",
    description="Added in 25.19.0. Configuration for rolling update strategy.",
)
class RollingUpdateConfigInputGQL:
    max_surge: int = 1
    max_unavailable: int = 0

    def to_spec(self) -> RollingUpdateSpec:
        return RollingUpdateSpec(
            max_surge=self.max_surge,
            max_unavailable=self.max_unavailable,
        )


@strawberry.input(
    name="BlueGreenConfigInput",
    description="Added in 25.19.0. Configuration for blue-green deployment strategy.",
)
class BlueGreenConfigInputGQL:
    auto_promote: bool = False
    promote_delay_seconds: int = 0

    def to_spec(self) -> BlueGreenSpec:
        return BlueGreenSpec(
            auto_promote=self.auto_promote,
            promote_delay_seconds=self.promote_delay_seconds,
        )


# ========== Deployment Policy Mutation Types ==========


@strawberry.input(
    name="CreateDeploymentPolicyInput",
    description="Added in 26.3.0. Input for creating a deployment policy.",
)
class CreateDeploymentPolicyInput:
    deployment_id: ID
    strategy: DeploymentStrategyTypeGQL
    rollback_on_failure: bool = False
    rolling_update: RollingUpdateConfigInputGQL | None = None
    blue_green: BlueGreenConfigInputGQL | None = None

    def to_policy_config(self) -> DeploymentPolicyConfig:
        """Convert to DeploymentPolicyConfig for service layer."""
        strategy = DeploymentStrategy(self.strategy.value)
        match strategy:
            case DeploymentStrategy.ROLLING:
                if self.rolling_update is None:
                    raise InvalidAPIParameters(
                        "rolling_update config required for ROLLING strategy"
                    )
                return DeploymentPolicyConfig(
                    strategy=strategy,
                    strategy_spec=self.rolling_update.to_spec(),
                    rollback_on_failure=self.rollback_on_failure,
                )
            case DeploymentStrategy.BLUE_GREEN:
                if self.blue_green is None:
                    raise InvalidAPIParameters("blue_green config required for BLUE_GREEN strategy")
                return DeploymentPolicyConfig(
                    strategy=strategy,
                    strategy_spec=self.blue_green.to_spec(),
                    rollback_on_failure=self.rollback_on_failure,
                )


@strawberry.input(
    name="UpdateDeploymentPolicyInput",
    description="Added in 26.3.0. Input for updating a deployment policy.",
)
class UpdateDeploymentPolicyInput:
    id: ID
    strategy: DeploymentStrategyTypeGQL | None = None
    rollback_on_failure: bool | None = None
    rolling_update: RollingUpdateConfigInputGQL | None = None
    blue_green: BlueGreenConfigInputGQL | None = None

    def to_updater_spec(self) -> DeploymentPolicyUpdaterSpec:
        """Convert to DeploymentPolicyUpdaterSpec for service layer."""
        spec = DeploymentPolicyUpdaterSpec()
        if self.strategy is not None:
            spec.strategy = OptionalState[DeploymentStrategy].update(
                DeploymentStrategy(self.strategy.value)
            )
        if self.rollback_on_failure is not None:
            spec.rollback_on_failure = OptionalState[bool].update(self.rollback_on_failure)
        if self.rolling_update is not None:
            spec.strategy_spec = OptionalState[RollingUpdateSpec | BlueGreenSpec].update(
                self.rolling_update.to_spec()
            )
        if self.blue_green is not None:
            spec.strategy_spec = OptionalState[RollingUpdateSpec | BlueGreenSpec].update(
                self.blue_green.to_spec()
            )
        return spec


@strawberry.type(
    name="CreateDeploymentPolicyPayload",
    description="Added in 26.3.0. Payload for creating a deployment policy.",
)
class CreateDeploymentPolicyPayload:
    deployment_policy: DeploymentPolicyGQL


@strawberry.type(
    name="UpdateDeploymentPolicyPayload",
    description="Added in 26.3.0. Payload for updating a deployment policy.",
)
class UpdateDeploymentPolicyPayload:
    deployment_policy: DeploymentPolicyGQL
