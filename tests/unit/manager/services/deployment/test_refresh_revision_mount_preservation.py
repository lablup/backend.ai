"""
Unit tests for ``_build_creator_from_revision_data``.

Tests verify that the rebuilder used by
``DeploymentService.admin_refresh_deployment_revisions`` preserves mount
identity (``extra_mounts`` and ``vfolder_subpath``) when projecting an
existing revision back into a ``ModelRevisionCreator``.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import (
    ClusterMode,
    MountInfoEntry,
    MountPermission,
    ResourceSlot,
)
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    ExecutionData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ResourceConfigData,
)
from ai.backend.manager.services.deployment.service import (
    _build_creator_from_revision_data,
)


class RefreshRevisionBaseFixtures:
    """Base class containing shared fixtures for refresh-revision rebuilder tests."""

    @pytest.fixture
    def model_vfolder_id(self) -> VFolderUUID:
        """Model vfolder ID referenced by the persisted revision."""
        return VFolderUUID(uuid.uuid4())

    @pytest.fixture
    def revision_data_factory(
        self, model_vfolder_id: VFolderUUID
    ) -> Callable[..., ModelRevisionData]:
        """Build a ModelRevisionData with configurable mount metadata."""

        def make(
            *,
            extra_mounts: list[MountInfoEntry] | None = None,
            vfolder_subpath: str | None = None,
            model_mount_perm: MountPermission | None = MountPermission.READ_WRITE,
        ) -> ModelRevisionData:
            return ModelRevisionData(
                id=DeploymentRevisionID(uuid.uuid4()),
                deployment_id=DeploymentID(uuid.uuid4()),
                revision_number=2,
                created_at=datetime(2026, 5, 26, tzinfo=UTC),
                image_id=ImageID(uuid.uuid4()),
                cluster_config=ClusterConfigData(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigData(
                    resource_group_name="default",
                    resource_slot=ResourceSlot(),
                ),
                model_runtime_config=ModelRuntimeConfigData(
                    runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
                ),
                execution=ExecutionData(
                    startup_command=None,
                    bootstrap_script=None,
                    callback_url=None,
                ),
                model_mount_config=ModelMountConfigData(
                    vfolder_id=model_vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                    extra_mounts=extra_mounts or [],
                    model_mount_perm=model_mount_perm,
                    subpath=vfolder_subpath,
                ),
                revision_preset=PresetAttributionData(preset_id=None, values=[]),
                model_definition=None,
            )

        return make


class TestBuildCreatorFromRevisionData(RefreshRevisionBaseFixtures):
    """Tests for ``_build_creator_from_revision_data``."""

    def test_extra_mounts_are_projected_onto_creator(
        self,
        revision_data_factory: Callable[..., ModelRevisionData],
    ) -> None:
        """Each extra mount survives verbatim (vfolder, destination, perm, subpath)."""
        vfolder_a = VFolderUUID(uuid.uuid4())
        vfolder_b = VFolderUUID(uuid.uuid4())
        revision = revision_data_factory(
            extra_mounts=[
                MountInfoEntry(
                    vfolder_id=vfolder_a,
                    mount_destination="/data",
                    mount_perm=MountPermission.READ_ONLY,
                    subpath=None,
                ),
                MountInfoEntry(
                    vfolder_id=vfolder_b,
                    mount_destination="/workspace",
                    mount_perm=MountPermission.READ_WRITE,
                    subpath="checkpoints",
                ),
            ],
        )

        creator = _build_creator_from_revision_data(revision)

        assert [m.vfolder_id for m in creator.mounts.extra_mounts] == [vfolder_a, vfolder_b]
        assert [m.mount_destination for m in creator.mounts.extra_mounts] == [
            "/data",
            "/workspace",
        ]
        assert [m.mount_perm for m in creator.mounts.extra_mounts] == [
            MountPermission.READ_ONLY,
            MountPermission.READ_WRITE,
        ]
        assert [m.subpath for m in creator.mounts.extra_mounts] == [None, "checkpoints"]

    def test_vfolder_subpath_is_projected_onto_creator(
        self,
        revision_data_factory: Callable[..., ModelRevisionData],
    ) -> None:
        """Non-root model vfolder subpath survives the rebuild."""
        revision = revision_data_factory(vfolder_subpath="release/v3")

        creator = _build_creator_from_revision_data(revision)

        assert creator.mounts.vfolder_subpath == "release/v3"

    def test_empty_mount_metadata_round_trips(
        self,
        revision_data_factory: Callable[..., ModelRevisionData],
    ) -> None:
        """Empty extra_mounts and unset subpath stay empty/None (no false injection)."""
        revision = revision_data_factory()

        creator = _build_creator_from_revision_data(revision)

        assert creator.mounts.extra_mounts == []
        assert creator.mounts.vfolder_subpath is None
