"""Unit tests for deployment revision validator rules."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import ClusterMode, MountPermission, ResourceSlot, SlotName
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionSpec,
    MountMetadata,
    ResourceSpec,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.deployment.creators.revision import (
    DeploymentRevisionCreatorSpec,
)
from ai.backend.manager.sokovan.deployment.validators import (
    DeploymentRevisionValidationContext,
    RequiredResourceSlotRule,
)


def _creator_spec(resource_slots: dict[str, int]) -> DeploymentRevisionCreatorSpec:
    return DeploymentRevisionCreatorSpec(
        deployment_id=DeploymentID(uuid4()),
        image_id=ImageID(uuid4()),
        resource_group="default",
        resource_slots=ResourceSlot(resource_slots),
        resource_opts={},
        cluster_mode=ClusterMode.SINGLE_NODE.value,
        cluster_size=1,
        model_vfolder_id=VFolderUUID(uuid4()),
        model_mount_destination="/models",
        model_mount_perm=MountPermission.READ_ONLY,
        vfolder_subpath=None,
        model_definition_path=None,
        model_definition=None,
        startup_command=None,
        bootstrap_script=None,
        environ={},
        callback_url=None,
        runtime_variant_id=RuntimeVariantID(uuid4()),
        extra_mounts=[],
    )


def _legacy_spec(resource_slots: dict[str, int]) -> ModelRevisionSpec:
    return ModelRevisionSpec(
        image_id=ImageID(uuid4()),
        resource_spec=ResourceSpec(
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            resource_slots=resource_slots,
            resource_opts=None,
        ),
        mounts=MountMetadata(
            model_vfolder_id=VFolderUUID(uuid4()),
            model_definition_path=None,
            model_mount_destination="/models",
            extra_mounts=[],
            model_mount_perm=None,
        ),
        execution=ExecutionSpec(runtime_variant_id=RuntimeVariantID(uuid4())),
        model_definition=None,
    )


class TestRequiredResourceSlotRule:
    @pytest.fixture
    def validation_context(self) -> DeploymentRevisionValidationContext:
        return DeploymentRevisionValidationContext(
            required_slot_names=frozenset({SlotName("cpu"), SlotName("mem")})
        )

    @pytest.fixture
    def rule(self) -> RequiredResourceSlotRule:
        return RequiredResourceSlotRule()

    def test_v2_passes_with_required_slots(
        self,
        validation_context: DeploymentRevisionValidationContext,
        rule: RequiredResourceSlotRule,
    ) -> None:
        spec = _creator_spec({"cpu": 1, "mem": 1024})
        rule.validate(spec, validation_context)

    @pytest.mark.parametrize(
        ("resource_slots", "expected_missing_slot"),
        [
            ({"cpu": 1}, "mem"),
            ({"cpu": 0, "mem": 1024}, "cpu"),
        ],
    )
    def test_v2_rejects_missing_or_zero_slots(
        self,
        resource_slots: dict[str, int],
        expected_missing_slot: str,
        validation_context: DeploymentRevisionValidationContext,
        rule: RequiredResourceSlotRule,
    ) -> None:
        spec = _creator_spec(resource_slots)

        with pytest.raises(InvalidAPIParameters, match=expected_missing_slot):
            rule.validate(spec, validation_context)

    def test_legacy_passes_with_required_slots(
        self,
        validation_context: DeploymentRevisionValidationContext,
        rule: RequiredResourceSlotRule,
    ) -> None:
        spec = _legacy_spec({"cpu": 1, "mem": 1024})

        rule.validate_legacy_revision_spec(spec, validation_context)

    @pytest.mark.parametrize(
        ("resource_slots", "expected_missing_slot"),
        [
            ({"cpu": 1}, "mem"),
            ({"cpu": 0, "mem": 1024}, "cpu"),
        ],
    )
    def test_legacy_rejects_missing_or_zero_slots(
        self,
        resource_slots: dict[str, int],
        expected_missing_slot: str,
        validation_context: DeploymentRevisionValidationContext,
        rule: RequiredResourceSlotRule,
    ) -> None:
        spec = _legacy_spec(resource_slots)

        with pytest.raises(InvalidAPIParameters, match=expected_missing_slot):
            rule.validate_legacy_revision_spec(spec, validation_context)
