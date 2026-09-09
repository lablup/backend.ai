"""Unit tests for DeploymentAdapter DTO conversions."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, override
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.config import ModelConfig, ModelDefinition, ModelServiceConfig
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.deployment import DeploymentEntityType, DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.v2.deployment.request import AdminSearchDeploymentsInput
from ai.backend.common.schema.deployment import RollingUpdateSpec
from ai.backend.common.types import ClusterMode, MountPermission, ResourceSlot
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.global_scope.validator.superadmin import (
    SuperAdminActionValidator,
)
from ai.backend.manager.actions.v2.ops.result import BulkFieldOpsResult, OwnedFieldsOpsResult
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.api.adapters.deployment.adapter import (
    DeploymentAdapter,
    _tristate_from_input,
)
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    DeploymentPolicyData,
    ExecutionData,
    ModelDeploymentAccessTokenData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ResourceConfigData,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.deployment.actions.scoped_search import (
    ScopedSearchDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.types import TriState

DENIED_TOKEN = DeploymentTokenID(uuid4())


class TestRevisionDataToDTO:
    """Tests for DeploymentAdapter._revision_data_to_dto conversion."""

    def test_model_definition_is_mapped_to_revision_dto(self) -> None:
        revision = ModelRevisionData(
            id=DeploymentRevisionID(uuid4()),
            deployment_id=DeploymentID(uuid4()),
            revision_number=1,
            cluster_config=ClusterConfigData(
                mode=ClusterMode.SINGLE_NODE,
                size=1,
            ),
            resource_config=ResourceConfigData(
                resource_group_name="default",
                resource_slot=ResourceSlot({"cpu": "2"}),
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant_id=RuntimeVariantID(uuid4()),
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=VFolderUUID(uuid4()),
                mount_destination="/models",
                definition_path="model-definition.yaml",
                extra_mounts=[],
                model_mount_perm=MountPermission.READ_ONLY,
            ),
            model_definition=ModelDefinition(
                models=[
                    ModelConfig(
                        name="demo-model",
                        model_path="/models/demo",
                        service=ModelServiceConfig(
                            start_command="python serve.py",
                            port=8000,
                        ),
                    ),
                ],
            ),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            image_id=ImageID(uuid4()),
            execution=ExecutionData(
                startup_command=None,
                bootstrap_script=None,
                callback_url=None,
            ),
            revision_preset=PresetAttributionData(preset_id=None, values=[]),
        )

        dto = DeploymentAdapter._revision_data_to_dto(revision)

        assert dto.model_definition is not None
        assert dto.model_definition.models[0].name == "demo-model"
        service = dto.model_definition.models[0].service
        assert service is not None
        assert service.port == 8000
        assert service.command == "python serve.py"
        assert service.start_command == ["python", "serve.py"]


class TestTriStateFromInput:
    """Tests for _tristate_from_input(): Sentinel/None/value → NOP/NULLIFY/UPDATE."""

    def test_sentinel_yields_nop(self) -> None:
        result: TriState[Decimal] = _tristate_from_input(SENTINEL)
        assert result.is_nop()

    def test_none_yields_nullify(self) -> None:
        result: TriState[Decimal] = _tristate_from_input(None)
        assert result.is_nullify()

    def test_decimal_value_yields_update(self) -> None:
        result = _tristate_from_input(Decimal("0.5"))
        assert result.is_update()
        assert result.value() == Decimal("0.5")

    def test_uuid_value_yields_update(self) -> None:
        preset_id = uuid4()
        result = _tristate_from_input(preset_id)
        assert result.is_update()
        assert result.value() == preset_id

    def test_int_value_yields_update(self) -> None:
        result = _tristate_from_input(3)
        assert result.is_update()
        assert result.value() == 3


class _RecordingScopeValidator(ScopeActionValidator):
    """Lets every scoped read through and keeps the scopes it was asked about."""

    def __init__(self) -> None:
        self.seen: list[Sequence[ScopeRef]] = []

    @override
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        self.seen.append(action.scope_targets())


class TestDeploymentSearchGates:
    """my/project searches are answered by the scope gate, not the superadmin gate.

    The processors come from the production wiring with the global gate kept as is and
    the scope gate replaced by a recorder, so a regular user's search passing proves it
    left the global (superadmin) path and names the scope it is answered for.
    """

    @pytest.fixture
    def regular_user(self) -> UserData:
        return UserData(
            user_id=uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
            domain_id=DomainID(uuid4()),
        )

    @pytest.fixture
    def scope_gate(self) -> _RecordingScopeValidator:
        return _RecordingScopeValidator()

    @pytest.fixture
    def adapter(self, scope_gate: _RecordingScopeValidator) -> DeploymentAdapter:
        registry: ProcessorRegistry[Any] = ProcessorRegistry(
            ProcessorDependencies(
                monitors=ActionMonitors(),
                validators=ActionValidators(
                    scope=[scope_gate],
                    global_scope=[SuperAdminActionValidator()],
                ),
                repository=OpsRepository(MagicMock()),
            )
        )
        service = MagicMock()
        service.scoped_search_deployments = AsyncMock(
            return_value=ScopedSearchDeploymentsActionResult(
                data=[], total_count=0, has_next_page=False, has_previous_page=False
            )
        )
        processors = MagicMock()
        processors.deployment = DeploymentProcessors(
            registry.group(GroupMeta(DeploymentEntityType())), service
        )
        return DeploymentAdapter(processors.deployment, MagicMock())

    async def test_my_search_is_answered_for_the_user_scope(
        self,
        adapter: DeploymentAdapter,
        scope_gate: _RecordingScopeValidator,
        regular_user: UserData,
    ) -> None:
        with with_user(regular_user):
            payload = await adapter.my_search(AdminSearchDeploymentsInput(limit=10, offset=0))

        assert payload.total_count == 0
        assert scope_gate.seen == [
            [ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=regular_user.user_id)]
        ]

    async def test_project_search_is_answered_for_the_project_scope(
        self,
        adapter: DeploymentAdapter,
        scope_gate: _RecordingScopeValidator,
        regular_user: UserData,
    ) -> None:
        project_id = uuid4()
        with with_user(regular_user):
            payload = await adapter.project_search(
                project_id, AdminSearchDeploymentsInput(limit=10, offset=0)
            )

        assert payload.total_count == 0
        assert scope_gate.seen == [[ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id)]]

    async def test_admin_search_keeps_the_superadmin_gate(
        self,
        adapter: DeploymentAdapter,
        regular_user: UserData,
    ) -> None:
        with with_user(regular_user), pytest.raises(InsufficientPrivilege):
            await adapter.admin_search(AdminSearchDeploymentsInput(limit=10, offset=0))


class TestFieldBatchLoads:
    """The field DataLoaders answer per named row, each checked through its deployment."""

    @pytest.fixture
    def token(self) -> ModelDeploymentAccessTokenData:
        return ModelDeploymentAccessTokenData(
            id=uuid4(),
            token="tok",
            expires_at=None,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        )

    @pytest.fixture
    def denial(self) -> GenericForbidden:
        return GenericForbidden("no read on this deployment")

    @pytest.fixture
    def adapter(
        self, token: ModelDeploymentAccessTokenData, denial: GenericForbidden
    ) -> tuple[DeploymentAdapter, MagicMock]:
        processors = MagicMock()
        processors.deployment.bulk_get_access_tokens.run = AsyncMock(
            return_value=BulkFieldOpsResult(
                successes={DeploymentTokenID(token.id): token},
                errors={DENIED_TOKEN: denial},
            )
        )
        return DeploymentAdapter(processors.deployment, MagicMock()), processors

    async def test_access_tokens_answer_per_id(
        self,
        adapter: tuple[DeploymentAdapter, MagicMock],
        token: ModelDeploymentAccessTokenData,
        denial: GenericForbidden,
    ) -> None:
        deployment_adapter, processors = adapter
        absent = DeploymentTokenID(uuid4())

        nodes = await deployment_adapter.batch_load_access_tokens_by_ids([
            DeploymentTokenID(token.id),
            DENIED_TOKEN,
            absent,
        ])

        node, refused, missing = nodes
        assert node is not None and not isinstance(node, Exception)
        assert node.id == token.id
        # A denial reaches the resolver; an id matching nothing stays None.
        assert refused is denial
        assert missing is None
        action = processors.deployment.bulk_get_access_tokens.run.await_args.args[0]
        assert list(action.field_ids()) == [
            DeploymentTokenID(token.id),
            DENIED_TOKEN,
            DeploymentTokenID(absent),
        ]

    async def test_a_batch_naming_no_row_is_every_id_missing(
        self, adapter: tuple[DeploymentAdapter, MagicMock]
    ) -> None:
        deployment_adapter, processors = adapter
        processors.deployment.bulk_get_access_tokens.run = AsyncMock(
            side_effect=EntityNotFoundError("No field row matches the given ids")
        )

        assert await deployment_adapter.batch_load_access_tokens_by_ids([
            DeploymentTokenID(uuid4()),
            DeploymentTokenID(uuid4()),
        ]) == [
            None,
            None,
        ]

    async def test_no_ids_read_nothing(self, adapter: tuple[DeploymentAdapter, MagicMock]) -> None:
        deployment_adapter, processors = adapter
        assert await deployment_adapter.batch_load_access_tokens_by_ids([]) == []
        processors.deployment.bulk_get_access_tokens.run.assert_not_awaited()

    async def test_policies_answer_per_deployment(self) -> None:
        deployment_id = DeploymentID(uuid4())
        policy = DeploymentPolicyData(
            id=uuid4(),
            endpoint=deployment_id,
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        processors = MagicMock()
        processors.deployment.bulk_get_deployment_policies.run = AsyncMock(
            return_value=OwnedFieldsOpsResult(designated={deployment_id: policy})
        )
        deployment_adapter = DeploymentAdapter(processors.deployment, MagicMock())
        without_policy = DeploymentID(uuid4())

        nodes = await deployment_adapter.batch_load_policies_by_endpoint_ids([
            deployment_id,
            without_policy,
        ])

        node, none = nodes
        assert node is not None and node.id == policy.id
        assert none is None
        action = processors.deployment.bulk_get_deployment_policies.run.await_args.args[0]
        assert list(action.owner_ids()) == [deployment_id, DeploymentID(without_policy)]
