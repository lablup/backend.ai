"""Write specs for a revision of a deployment."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.config import ModelConfig, ModelDefinition
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import ClusterMode, MountPermission, ResourceSlot
from ai.backend.manager.data.deployment.types import DeploymentInfo, ModelRevisionData
from ai.backend.manager.models.deployment_revision.creators import DeploymentRevisionCreator
from bai_scenario.seeds.seeder import SeedField


@dataclass(frozen=True)
class SeedRevisionOf(SeedField[DeploymentInfo, ModelRevisionData]):
    """One revision of the deployment, numbered one past its last.

    The image, folder, runtime and group are values earlier rows answered; this seed
    names none of its own. It runs on one node and mounts the folder read-write.
    """

    image_id: ImageID
    folder_id: VFolderUUID
    runtime_variant_id: RuntimeVariantID
    resource_group: str
    slots: tuple[tuple[str, Decimal], ...]
    model_name: str
    mounted_at: str

    @override
    def kind(self) -> str:
        return "리비전 하나를 갖는다"

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> DeploymentRevisionCreator:
        return DeploymentRevisionCreator(
            image_id=self.image_id,
            resource_group=self.resource_group,
            resource_slots=ResourceSlot(dict(self.slots)),
            resource_opts={},
            cluster_mode=ClusterMode.SINGLE_NODE.value,
            cluster_size=1,
            model_vfolder_id=self.folder_id,
            model_mount_destination=self.mounted_at,
            model_mount_perm=MountPermission.READ_WRITE,
            vfolder_subpath=None,
            model_definition_path=None,
            model_definition=ModelDefinition(
                models=[ModelConfig(name=self.model_name, model_path=self.mounted_at)]
            ),
            startup_command=None,
            bootstrap_script=None,
            environ={},
            callback_url=None,
            runtime_variant_id=self.runtime_variant_id,
            extra_mounts=[],
        )
