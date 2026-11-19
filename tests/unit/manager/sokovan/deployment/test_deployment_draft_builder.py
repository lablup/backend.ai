from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelServiceConfig,
)
from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    MountPermission,
    ResourceSlot,
)
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkData,
    DeploymentOptions,
    DeploymentState,
    ExecutionData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ReplicaData,
    ResourceConfigData,
)
from ai.backend.manager.data.session.creation import (
    DeploymentContext,
    ResolvedPresetValues,
    UserContext,
)
from ai.backend.manager.data.session.draft import KernelExecutionSpecDraft, SchedulingTargetDraft
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.sokovan.deployment.deployment_draft_builder import (
    DeploymentSessionDraftBuilder,
)


def _revision_data(model_definition: ModelDefinition | None) -> ModelRevisionData:
    revision = MagicMock(spec=ModelRevisionData)
    revision.model_definition = model_definition
    return cast(ModelRevisionData, revision)


def _context(args: list[str] | None) -> DeploymentContext:
    """Build a ``DeploymentContext`` with only the preset-args slice the
    builder method touches; everything else stays a ``MagicMock`` because
    ``_model_definition_payload`` does not read it."""
    context = MagicMock(spec=DeploymentContext)
    context.resolved_presets = (
        ResolvedPresetValues(environ={}, args=args) if args is not None else None
    )
    return cast(DeploymentContext, context)


class TestModelDefinitionPayload:
    """Tests scoped to the builder method only — the merge invariants
    themselves (identity on empty args, immutability, multi-model fan-out,
    ``service=None`` pass-through, ``start_command=None`` handling) are
    covered by ``TestModelDefinitionWithArgsAppended`` in
    ``tests/unit/common/test_config.py`` and not duplicated here.
    """

    @pytest.fixture
    def vllm_revision(self) -> ModelRevisionData:
        return _revision_data(
            ModelDefinition(
                models=[
                    ModelConfig(
                        name="vllm-model",
                        model_path="/models",
                        service=ModelServiceConfig(
                            port=8000,
                            start_command="vllm serve /models",
                        ),
                    )
                ]
            )
        )

    async def test_returns_none_when_revision_has_no_definition(self) -> None:
        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            _revision_data(None),
            _context(None),
        )

        assert payload is None

    @pytest.mark.parametrize(
        ("args", "expected_start_command"),
        [
            pytest.param(None, "vllm serve /models", id="presets-absent"),
            pytest.param([], "vllm serve /models", id="presets-empty"),
            pytest.param(
                ["--max-model-len", "4096"],
                "vllm serve /models --max-model-len 4096",
                id="presets-with-args",
            ),
        ],
    )
    async def test_reads_args_from_context_into_dict_payload(
        self,
        vllm_revision: ModelRevisionData,
        args: list[str] | None,
        expected_start_command: str,
    ) -> None:
        # Builder wiring contract: pulls args from ``context.resolved_presets``
        # (handling both ``None`` and empty-list shapes) and returns a dict
        # ready for the kernel — i.e., ``model_dump`` has been called.
        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            vllm_revision, _context(args)
        )

        assert payload is not None
        assert isinstance(payload, dict)
        assert payload["models"][0]["service"]["start_command"] == expected_start_command

    async def test_args_tokenized_per_token_not_concatenated(
        self,
        vllm_revision: ModelRevisionData,
    ) -> None:
        # Regression guard for argument appending: preset tokens are shell-quoted
        # before they are appended to the command string.
        tokens = ["--port", "8000", "--max-model-len", "4096"]

        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            vllm_revision, _context(tokens)
        )

        assert payload is not None
        cmd = payload["models"][0]["service"]["start_command"]
        assert cmd == "vllm serve /models --port 8000 --max-model-len 4096"


class TestKernelGroups:
    """Multi-node deployment lays out 1 main + (cluster_size - 1) sub."""

    @pytest.fixture
    def execution_spec(self) -> KernelExecutionSpecDraft:
        return KernelExecutionSpecDraft()

    @pytest.fixture
    def kernel_draft_builder(self) -> DeploymentSessionDraftBuilder:
        return DeploymentSessionDraftBuilder()

    def test_single_node_yields_one_main_group(
        self,
        execution_spec: KernelExecutionSpecDraft,
        kernel_draft_builder: DeploymentSessionDraftBuilder,
    ) -> None:
        groups = kernel_draft_builder._resolve_kernel_groups(
            cluster_size=1, execution_spec=execution_spec
        )

        assert len(groups) == 1
        assert groups[0].role == DEFAULT_ROLE
        assert groups[0].replica_count == 1

    @pytest.mark.parametrize(
        ("cluster_size", "expected_sub_replicas"),
        [
            pytest.param(2, 1, id="size-2"),
            pytest.param(3, 2, id="size-3"),
            pytest.param(5, 4, id="size-5"),
        ],
    )
    def test_multi_node_splits_main_and_sub(
        self,
        execution_spec: KernelExecutionSpecDraft,
        cluster_size: int,
        expected_sub_replicas: int,
        kernel_draft_builder: DeploymentSessionDraftBuilder,
    ) -> None:
        groups = kernel_draft_builder._resolve_kernel_groups(
            cluster_size=cluster_size, execution_spec=execution_spec
        )

        assert len(groups) == 2
        main, sub = groups
        assert main.role == DEFAULT_ROLE
        assert main.replica_count == 1
        assert sub.role == "sub"
        assert sub.replica_count == expected_sub_replicas


class TestResolveMounts:
    """The model vfolder mount uses the permission frozen on the revision."""

    @staticmethod
    def _revision(model_mount_perm: MountPermission) -> ModelRevisionData:
        revision = MagicMock(spec=ModelRevisionData)
        mount_config = MagicMock()
        mount_config.vfolder_id = VFolderUUID(uuid4())
        mount_config.mount_destination = "/models"
        mount_config.model_mount_perm = model_mount_perm
        mount_config.subpath = None
        mount_config.extra_mounts = []
        revision.model_mount_config = mount_config
        return cast(ModelRevisionData, revision)

    def test_uses_stored_model_mount_perm(self) -> None:
        mounts = DeploymentSessionDraftBuilder._resolve_mounts(
            self._revision(MountPermission.READ_WRITE)
        )
        assert mounts[0].mount_perm == MountPermission.READ_WRITE

    def test_read_only_revision_mounts_read_only(self) -> None:
        mounts = DeploymentSessionDraftBuilder._resolve_mounts(
            self._revision(MountPermission.READ_ONLY)
        )
        assert mounts[0].mount_perm == MountPermission.READ_ONLY


class TestSchedulingTarget:
    """The route session is placed by the deployment's designated agents and policy."""

    @pytest.fixture
    def revision(self) -> ModelRevisionData:
        return ModelRevisionData(
            id=DeploymentRevisionID(uuid4()),
            deployment_id=DeploymentID(uuid4()),
            revision_number=1,
            created_at=datetime(2026, 10, 21, tzinfo=UTC),
            image_id=ImageID(uuid4()),
            cluster_config=ClusterConfigData(mode=ClusterMode.SINGLE_NODE, size=1),
            resource_config=ResourceConfigData(
                resource_group_name="default",
                resource_slot=ResourceSlot(),
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant_id=RuntimeVariantID(uuid4())
            ),
            execution=ExecutionData(startup_command=None, bootstrap_script=None, callback_url=None),
            model_mount_config=ModelMountConfigData(
                vfolder_id=VFolderUUID(uuid4()),
                mount_destination="/models",
                definition_path="model-definition.yaml",
                extra_mounts=[],
                model_mount_perm=MountPermission.READ_ONLY,
                subpath=None,
            ),
            revision_preset=PresetAttributionData(preset_id=None, values=[]),
        )

    @pytest.fixture
    def context(self) -> DeploymentContext:
        context = MagicMock(spec=DeploymentContext)
        context.session_owner = UserContext(
            uuid=uuid4(),
            access_key=AccessKey("AKIATEST"),
            role="user",
            sudo_session_enabled=False,
        )
        context.domain_id = DomainID(uuid4())
        context.group_id = uuid4()
        context.resource_group_id = ResourceGroupID(uuid4())
        context.resolved_presets = None
        return cast(DeploymentContext, context)

    @staticmethod
    def _deployment(policy: AgentSelectionPolicy) -> DeploymentInfo:
        return DeploymentInfo(
            id=DeploymentID(uuid4()),
            metadata=DeploymentMetadata(
                name="deployment",
                domain="default",
                project=uuid4(),
                resource_group="default",
                created_user=uuid4(),
                session_owner=uuid4(),
                created_at=None,
            ),
            state=DeploymentState(
                lifecycle=EndpointLifecycle.READY,
                scaling_state=ScalingState.STABLE,
                retry_count=0,
            ),
            replica=ReplicaData(replica_count=1, desired_replica_count=1),
            network=DeploymentNetworkData(
                open_to_public=False,
                access_token_ids=None,
                url=None,
                preferred_domain_name=None,
            ),
            options=DeploymentOptions(agent_selection_policy=policy),
        )

    def _scheduling_target(
        self,
        deployment: DeploymentInfo,
        designated_agents: list[AgentId],
        revision: ModelRevisionData,
        context: DeploymentContext,
    ) -> SchedulingTargetDraft | None:
        draft = DeploymentSessionDraftBuilder.build(
            deployment_info=deployment,
            context=context,
            route_id=uuid4(),
            target_revision=revision,
            session_group_id=None,
            designated_agents=designated_agents,
        )
        return draft.resource_spec.resource.options.scheduling_target

    @pytest.mark.parametrize(
        "policy",
        [AgentSelectionPolicy.STRICT, AgentSelectionPolicy.PREFERRED],
        ids=["strict", "preferred"],
    )
    def test_carries_the_designated_agents_and_the_policy(
        self,
        revision: ModelRevisionData,
        context: DeploymentContext,
        policy: AgentSelectionPolicy,
    ) -> None:
        agents = [AgentId("i-agent-a"), AgentId("i-agent-b")]

        target = self._scheduling_target(self._deployment(policy), agents, revision, context)

        assert target == SchedulingTargetDraft(
            designated_agents=tuple(agents), agent_selection_policy=policy
        )

    def test_a_deployment_without_designation_leaves_the_agents_open(
        self,
        revision: ModelRevisionData,
        context: DeploymentContext,
    ) -> None:
        deployment = self._deployment(AgentSelectionPolicy.PREFERRED)

        target = self._scheduling_target(deployment, [], revision, context)

        assert target == SchedulingTargetDraft(
            designated_agents=(), agent_selection_policy=AgentSelectionPolicy.PREFERRED
        )
