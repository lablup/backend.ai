"""Tests for InferenceModelFolderRule."""

import uuid
from collections.abc import Callable
from pathlib import PurePosixPath

import pytest

from ai.backend.common.types import (
    MountPermission,
    SessionTypes,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    ContainerUserInfo,
    ScalingGroupNetworkInfo,
    SessionCreationContext,
    SessionCreationSpec,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.inference import (
    InferenceModelFolderRule,
)


def _make_vfolder_mount(
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL,
    name: str = "test-folder",
) -> VFolderMount:
    return VFolderMount(
        name=name,
        vfid=VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()),
        vfsubpath=PurePosixPath("."),
        host_path=PurePosixPath("/mnt/vfolder"),
        kernel_path=PurePosixPath("/home/work/folder"),
        mount_perm=MountPermission.READ_ONLY,
        usage_mode=usage_mode,
    )


@pytest.fixture
def basic_context() -> SessionCreationContext:
    return SessionCreationContext(
        scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
        allowed_scaling_groups=[
            AllowedScalingGroup(
                name="default-sg", is_private=False, scheduler_opts=ScalingGroupOpts()
            ),
        ],
        image_infos={},
        vfolder_mounts=[],
        dotfile_data={},
        container_user_info=ContainerUserInfo(),
    )


class TestInferenceModelFolderRule:
    """Test cases for InferenceModelFolderRule."""

    def test_non_inference_session_skips_validation(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Non-INFERENCE session types should pass without any model folder."""
        rule = InferenceModelFolderRule()
        spec = session_spec_factory(session_type=SessionTypes.INTERACTIVE)

        rule.validate(spec, basic_context)

    def test_inference_with_model_folder_passes(
        self,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """INFERENCE session with a model folder should pass."""
        rule = InferenceModelFolderRule()
        spec = session_spec_factory(session_type=SessionTypes.INFERENCE)
        context = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
            allowed_scaling_groups=[],
            image_infos={},
            vfolder_mounts=[_make_vfolder_mount(VFolderUsageMode.MODEL, "my-model")],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        rule.validate(spec, context)

    def test_inference_without_model_folder_raises(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """INFERENCE session without any model folder should raise InvalidAPIParameters."""
        rule = InferenceModelFolderRule()
        spec = session_spec_factory(session_type=SessionTypes.INFERENCE)

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context)
        assert "model-type virtual folder" in str(exc_info.value)

    def test_inference_custom_variant_without_model_folder_passes(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """INFERENCE session with runtime_variant=custom should pass even without model folder."""
        rule = InferenceModelFolderRule()
        spec = session_spec_factory(
            session_type=SessionTypes.INFERENCE,
            creation_spec={"runtime_variant": "custom"},
        )

        rule.validate(spec, basic_context)

    def test_inference_no_runtime_variant_without_model_folder_raises(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """INFERENCE session with runtime_variant=None should still require a model folder."""
        rule = InferenceModelFolderRule()
        spec = session_spec_factory(
            session_type=SessionTypes.INFERENCE,
            creation_spec={},
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context)
        assert "model-type virtual folder" in str(exc_info.value)

    def test_inference_with_general_folder_only_raises(
        self,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """INFERENCE session with only GENERAL folders (no MODEL) should raise."""
        rule = InferenceModelFolderRule()
        spec = session_spec_factory(session_type=SessionTypes.INFERENCE)
        context = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
            allowed_scaling_groups=[],
            image_infos={},
            vfolder_mounts=[
                _make_vfolder_mount(VFolderUsageMode.GENERAL, "my-data"),
                _make_vfolder_mount(VFolderUsageMode.DATA, "shared-data"),
            ],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        with pytest.raises(InvalidAPIParameters):
            rule.validate(spec, context)
