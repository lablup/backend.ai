"""Write specs for an image."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.image.creators import ImageAliasCreator, ImageCreator
from bai_scenario.seeds.seeder import (
    Naming,
    TestSeedFieldCreator,
    TestSeedRowFrom,
    TestSeedRowFromTwo,
)


@dataclass(frozen=True)
class TestSeedImage(TestSeedRowFrom[ContainerRegistryData, ImageData]):
    """An image of the given registry. A session names one to run."""

    name_hint: str = "image"
    architecture: str = "x86_64"
    status: ImageStatus = ImageStatus.ALIVE
    customized: bool = False
    creator_id: UserID | None = None
    accelerators: str | None = None

    @override
    def kind(self) -> str:
        return "이미지"

    @override
    def detail(self) -> str:
        marks = [f"{self.architecture} 이미지"]
        if self.status is not ImageStatus.ALIVE:
            marks.append(f"상태는 {self.status.value}")
        if self.customized:
            marks.append("커스터마이즈된 이미지라 소유자가 있다")
        if self.accelerators is not None:
            marks.append(f"가속기는 {self.accelerators}")
        return ", ".join(marks)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: ContainerRegistryData) -> ImageCreator:
        return ImageCreator(
            name=name,
            project=None,
            architecture=self.architecture,
            registry_id=ContainerRegistryID(source.id),
            registry=source.registry_name,
            image=name,
            tag="latest",
            config_digest=f"sha256:{name:>064}".replace(" ", "0"),
            size_bytes=0,
            labels={},
            type=ImageType.COMPUTE,
            status=self.status,
            customized=self.customized,
            creator_id=self.creator_id,
            accelerators=self.accelerators,
            registry_is_global=bool(source.is_global),
        )


@dataclass(frozen=True)
class TestSeedCommittedImage(TestSeedRowFromTwo[ContainerRegistryData, ProjectData, ImageData]):
    """An image a session commit made for the given user: it sits in the given registry
    and is owned by that user's personal project."""

    creator_id: UserID
    name_hint: str = "image"
    status: ImageStatus = ImageStatus.ALIVE

    @override
    def kind(self) -> str:
        return "커밋한 이미지"

    @override
    def detail(self) -> str:
        marks = ["커스터마이즈된 이미지라 소유자가 있다", "그 사람의 개인 프로젝트에 속한다"]
        if self.status is not ImageStatus.ALIVE:
            marks.append(f"상태는 {self.status.value}")
        return ", ".join(marks)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, first: ContainerRegistryData, second: ProjectData) -> ImageCreator:
        image = TestSeedImage(customized=True, creator_id=self.creator_id, status=self.status)
        return replace(image.seed(name, first), created_in_project_id=ProjectID(second.id))


@dataclass(frozen=True)
class TestSeedTaggedImage(TestSeedRowFrom[ContainerRegistryData, ImageData]):
    """An image registered under a tag of the given registry, as a scan would name it."""

    repository: str
    tag: str
    architecture: str = "x86_64"
    config_digest: str = "sha256:before-scan"

    @override
    def kind(self) -> str:
        return "이미지"

    @override
    def detail(self) -> str:
        return f"{self.architecture} 이미지, 설정 다이제스트는 {self.config_digest}"

    @override
    def name(self, naming: Naming) -> str:
        return f"{self.repository}:{self.tag}"

    @override
    def seed(self, name: str, source: ContainerRegistryData) -> ImageCreator:
        return ImageCreator(
            name=f"{source.registry_name}/{name}",
            project=source.project,
            architecture=self.architecture,
            registry_id=ContainerRegistryID(source.id),
            registry=source.registry_name,
            image=self.repository,
            tag=self.tag,
            config_digest=self.config_digest,
            size_bytes=0,
            labels={},
            type=ImageType.COMPUTE,
            registry_is_global=bool(source.is_global),
        )


@dataclass(frozen=True)
class TestSeedAlias(TestSeedFieldCreator[ImageData, ImageAliasData]):
    """One alias of an image.

    The alias column is unique across every image, and each scenario runs against its
    own copy of the schema, so a plain name is enough. A scenario that needs the name
    reads it off the row this laid.
    """

    alias: str = "seeded-alias"

    @override
    def kind(self) -> str:
        return f"별칭 {self.alias}"

    @override
    def owner_id(self, owner: ImageData) -> ImageID:
        return ImageID(owner.id)

    @override
    def seed(self) -> ImageAliasCreator:
        return ImageAliasCreator(alias=self.alias)
