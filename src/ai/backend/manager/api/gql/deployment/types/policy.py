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
    max_surge: int = strawberry.field(
        default=1,
        description="Maximum number of extra replicas that can be created above the desired count during an update. Defaults to 1.",
    )
    max_unavailable: int = strawberry.field(
        default=0,
        description="Maximum number of replicas that can be unavailable during an update. Defaults to 0.",
    )

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
    auto_promote: bool = strawberry.field(
        default=False,
        description="Whether to automatically promote the new (green) deployment after readiness checks pass. Defaults to false.",
    )
    promote_delay_seconds: int = strawberry.field(
        default=0,
        description="Number of seconds to wait before promoting the new deployment. Only effective when auto_promote is true. Defaults to 0.",
    )

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
class CreateDeploymentPolicyInputGQL:
    deployment_id: ID = strawberry.field(
        description="The ID of the deployment to associate with this policy.",
    )
    strategy: DeploymentStrategyTypeGQL = strawberry.field(
        description="The deployment strategy type (ROLLING or BLUE_GREEN).",
    )
    rollback_on_failure: bool = strawberry.field(
        default=False,
        description="Whether to automatically rollback to the previous version when the deployment fails. Defaults to false.",
    )
    rolling_update: RollingUpdateConfigInputGQL | None = strawberry.field(
        default=None,
        description="Configuration for rolling update strategy. Required when strategy is ROLLING. Must not be provided together with blue_green.",
    )
    blue_green: BlueGreenConfigInputGQL | None = strawberry.field(
        default=None,
        description="Configuration for blue-green deployment strategy. Required when strategy is BLUE_GREEN. Must not be provided together with rolling_update.",
    )

    def to_policy_config(self) -> DeploymentPolicyConfig:
        """Convert to DeploymentPolicyConfig for service layer."""
        if self.rolling_update is not None and self.blue_green is not None:
            raise InvalidAPIParameters(
                "Cannot provide both rolling_update and blue_green; only one strategy config is allowed."
            )
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
            case _:
                raise InvalidAPIParameters(f"Unsupported deployment strategy: {strategy}")


@strawberry.input(
    name="UpdateDeploymentPolicyInput",
    description="Added in 26.3.0. Input for updating a deployment policy.",
)
class UpdateDeploymentPolicyInputGQL:
    id: ID = strawberry.field(
        description="The ID of the deployment policy to update.",
    )
    strategy: DeploymentStrategyTypeGQL | None = strawberry.field(
        default=None,
        description="The new deployment strategy type. If changed, the corresponding strategy config (rolling_update or blue_green) should also be provided.",
    )
    rollback_on_failure: bool | None = strawberry.field(
        default=None,
        description="Whether to automatically rollback to the previous version when the deployment fails.",
    )
    rolling_update: RollingUpdateConfigInputGQL | None = strawberry.field(
        default=None,
        description="Updated configuration for rolling update strategy. Must not be provided together with blue_green.",
    )
    blue_green: BlueGreenConfigInputGQL | None = strawberry.field(
        default=None,
        description="Updated configuration for blue-green deployment strategy. Must not be provided together with rolling_update.",
    )

    def to_updater_spec(self) -> DeploymentPolicyUpdaterSpec:
        """Convert to DeploymentPolicyUpdaterSpec for service layer."""
        if self.rolling_update is not None and self.blue_green is not None:
            raise InvalidAPIParameters(
                "Cannot provide both rolling_update and blue_green; only one strategy config is allowed."
            )
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
class CreateDeploymentPolicyPayloadGQL:
    deployment_policy: DeploymentPolicyGQL


@strawberry.type(
    name="UpdateDeploymentPolicyPayload",
    description="Added in 26.3.0. Payload for updating a deployment policy.",
)
class UpdateDeploymentPolicyPayloadGQL:
    deployment_policy: DeploymentPolicyGQL
