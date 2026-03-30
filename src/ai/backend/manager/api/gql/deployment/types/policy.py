"""GraphQL types for DeploymentPolicy."""

from __future__ import annotations

from datetime import datetime

from strawberry import ID, UNSET
from strawberry.relay import NodeID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import (
    BlueGreenConfigInput as BlueGreenConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RollingUpdateConfigInput as RollingUpdateConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    UpsertDeploymentPolicyInput as UpsertDeploymentPolicyInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeploymentPolicyNode as DeploymentPolicyNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    UpdateDeploymentPolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    BlueGreenStrategySpecInfo,
    DeploymentStrategySpecInfo,
    RollingUpdateStrategySpecInfo,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    IntOrPercent as IntOrPercentDTO,
)
from ai.backend.common.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_interface,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.utils import dedent_strip

# Enum defined here to avoid circular import with deployment.py
DeploymentStrategyTypeGQL: type[DeploymentStrategy] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="This enum represents the deployment strategy type of a model deployment, indicating the strategy used for deployment.",
    ),
    DeploymentStrategy,
    name="DeploymentStrategyType",
)


# ========== IntOrPercent types ==========


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=dedent_strip("""
            A rolling-update budget value: either an absolute count or a percentage.
            Exactly one of 'count' or 'percent' is non-null.
        """),
    ),
    model=IntOrPercentDTO,
    name="IntOrPercent",
)
class IntOrPercentGQL:
    count: int | None
    percent: float | None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=dedent_strip("""
            Input for a rolling-update budget value (oneOf).
            Provide exactly one of 'count' (absolute replica count) or 'percent' (0.0-1.0 fraction).
        """),
    ),
    name="IntOrPercentInput",
    one_of=True,
)
class IntOrPercentInputGQL(PydanticInputMixin[IntOrPercentDTO]):
    count: int | None = UNSET
    percent: float | None = UNSET


# ========== Output Types (Response) ==========


@gql_pydantic_interface(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Base interface for deployment strategy specifications.",
    ),
    model=DeploymentStrategySpecInfo,
    name="DeploymentStrategySpec",
)
class DeploymentStrategySpecGQL:
    strategy: DeploymentStrategyTypeGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Rolling update strategy specification.",
    ),
    model=RollingUpdateStrategySpecInfo,
    name="RollingUpdateStrategySpec",
)
class RollingUpdateStrategySpecGQL(DeploymentStrategySpecGQL):
    strategy: DeploymentStrategyTypeGQL
    max_surge: IntOrPercentGQL
    max_unavailable: IntOrPercentGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Blue-green deployment strategy specification.",
    ),
    model=BlueGreenStrategySpecInfo,
    name="BlueGreenStrategySpec",
)
class BlueGreenStrategySpecGQL(DeploymentStrategySpecGQL):
    strategy: DeploymentStrategyTypeGQL
    auto_promote: bool
    promote_delay_seconds: int


@gql_node_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Deployment policy configuration."),
    name="DeploymentPolicy",
)
class DeploymentPolicyGQL(PydanticNodeMixin[DeploymentPolicyNodeDTO]):
    id: NodeID[str]
    strategy_spec: DeploymentStrategySpecGQL
    created_at: datetime
    updated_at: datetime


# ========== Input Types ==========


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Configuration for rolling update strategy. Defaults: max_surge=50%, max_unavailable=0%.",
        added_version="25.19.0",
    ),
    name="RollingUpdateConfigInput",
)
class RollingUpdateConfigInputGQL(PydanticInputMixin[RollingUpdateConfigInputDTO]):
    max_surge: IntOrPercentInputGQL | None = UNSET
    max_unavailable: IntOrPercentInputGQL | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Configuration for blue-green deployment strategy.", added_version="25.19.0"
    ),
    name="BlueGreenConfigInput",
)
class BlueGreenConfigInputGQL(PydanticInputMixin[BlueGreenConfigInputDTO]):
    auto_promote: bool = False
    promote_delay_seconds: int = 0


# ========== Mutation Input/Payload Types ==========


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=dedent_strip("""
            Input for creating or updating a deployment policy (upsert semantics).
            Specify the target deployment_id and the desired strategy type.
            Exactly one of rolling_update or blue_green must be provided,
            matching the chosen strategy type.
            If a policy already exists for the deployment, it is replaced entirely.
        """),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="UpdateDeploymentPolicyInput",
)
class UpdateDeploymentPolicyInputGQL(PydanticInputMixin[UpsertDeploymentPolicyInputDTO]):
    deployment_id: ID
    strategy: DeploymentStrategyTypeGQL
    rolling_update: RollingUpdateConfigInputGQL | None = None
    blue_green: BlueGreenConfigInputGQL | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Result payload returned after creating or updating a deployment policy. Contains the full deployment_policy object reflecting the applied configuration.",
    ),
    model=UpdateDeploymentPolicyPayloadDTO,
    name="UpdateDeploymentPolicyPayload",
)
class UpdateDeploymentPolicyPayloadGQL(PydanticOutputMixin[UpdateDeploymentPolicyPayloadDTO]):
    deployment_policy: DeploymentPolicyGQL
