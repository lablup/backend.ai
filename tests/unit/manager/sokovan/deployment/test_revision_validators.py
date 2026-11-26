"""Unit tests for deployment revision validator rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import (
    ClusterMode,
    MountInfoEntry,
    MountPermission,
    ResourceSlot,
    SlotName,
)
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionSpec,
    MountMetadata,
    ResourceSpec,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.deployment_revision.creators import (
    DeploymentRevisionCreator,
)
from ai.backend.manager.sokovan.deployment.validators.base import (
    DeploymentRevisionValidationContext,
)
from ai.backend.manager.sokovan.deployment.validators.no_parent_segment_in_mount_destination_rule import (
    NoParentSegmentInMountDestinationRule,
)
from ai.backend.manager.sokovan.deployment.validators.required_resource_slot_rule import (
    RequiredResourceSlotRule,
)


@dataclass(frozen=True)
class _MountDestinationsCase:
    name: str
    model_mount_destination: str
    extra_mount_destinations: list[str | None]


def _creator_spec(resource_slots: dict[str, int]) -> DeploymentRevisionCreator:
    return DeploymentRevisionCreator(
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


class TestNoParentSegmentInMountDestinationRule:
    @pytest.fixture
    def validation_context(self) -> DeploymentRevisionValidationContext:
        return DeploymentRevisionValidationContext()

    @pytest.fixture
    def rule(self) -> NoParentSegmentInMountDestinationRule:
        return NoParentSegmentInMountDestinationRule()

    @pytest.fixture
    def creator_mounting_at_case_destinations(
        self, case: _MountDestinationsCase
    ) -> DeploymentRevisionCreator:
        return replace(
            _creator_spec({"cpu": 1}),
            model_mount_destination=case.model_mount_destination,
            extra_mounts=[
                MountInfoEntry(vfolder_id=VFolderUUID(uuid4()), mount_destination=destination)
                for destination in case.extra_mount_destinations
            ],
        )

    @pytest.fixture
    def legacy_spec_mounting_at_case_destinations(
        self, case: _MountDestinationsCase
    ) -> ModelRevisionSpec:
        spec = _legacy_spec({"cpu": 1})
        return spec.model_copy(
            update={
                "mounts": replace(
                    spec.mounts,
                    model_mount_destination=case.model_mount_destination,
                    extra_mounts=[
                        MountInfoEntry(
                            vfolder_id=VFolderUUID(uuid4()), mount_destination=destination
                        )
                        for destination in case.extra_mount_destinations
                    ],
                )
            }
        )

    @pytest.mark.parametrize(
        "case",
        [
            _MountDestinationsCase(
                name="model-mount-destination",
                model_mount_destination="/models/../models",
                extra_mount_destinations=[],
            ),
            _MountDestinationsCase(
                name="extra-mount-destination",
                model_mount_destination="/models",
                extra_mount_destinations=[None, "/home/work/../data"],
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_v2_rejects_parent_segment(
        self,
        validation_context: DeploymentRevisionValidationContext,
        rule: NoParentSegmentInMountDestinationRule,
        creator_mounting_at_case_destinations: DeploymentRevisionCreator,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match=r"must not contain a '\.\.' segment"):
            rule.validate(creator_mounting_at_case_destinations, validation_context)

    @pytest.mark.parametrize(
        "case",
        [
            _MountDestinationsCase(
                name="model-mount-destination",
                model_mount_destination="/models/../models",
                extra_mount_destinations=[],
            ),
            _MountDestinationsCase(
                name="extra-mount-destination",
                model_mount_destination="/models",
                extra_mount_destinations=[None, "/home/work/../data"],
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_legacy_rejects_parent_segment(
        self,
        validation_context: DeploymentRevisionValidationContext,
        rule: NoParentSegmentInMountDestinationRule,
        legacy_spec_mounting_at_case_destinations: ModelRevisionSpec,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match=r"must not contain a '\.\.' segment"):
            rule.validate_legacy_revision_spec(
                legacy_spec_mounting_at_case_destinations, validation_context
            )

    @pytest.mark.parametrize(
        "case",
        [
            _MountDestinationsCase(
                name="without-parent-segment",
                model_mount_destination="/models",
                extra_mount_destinations=[None, "/home/work/data"],
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_v2_passes_without_parent_segment(
        self,
        validation_context: DeploymentRevisionValidationContext,
        rule: NoParentSegmentInMountDestinationRule,
        creator_mounting_at_case_destinations: DeploymentRevisionCreator,
    ) -> None:
        rule.validate(creator_mounting_at_case_destinations, validation_context)

    @pytest.mark.parametrize(
        "case",
        [
            _MountDestinationsCase(
                name="without-parent-segment",
                model_mount_destination="/models",
                extra_mount_destinations=[None, "/home/work/data"],
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_legacy_passes_without_parent_segment(
        self,
        validation_context: DeploymentRevisionValidationContext,
        rule: NoParentSegmentInMountDestinationRule,
        legacy_spec_mounting_at_case_destinations: ModelRevisionSpec,
    ) -> None:
        rule.validate_legacy_revision_spec(
            legacy_spec_mounting_at_case_destinations, validation_context
        )
