import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final, Optional, override

from aiodocker.docker import Docker

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.docker import DEFAULT_KERNEL_FEATURE, KernelFeatures, LabelName
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)

LDD_GLIBC_REGEX = re.compile(r"^ldd \([^\)]+\) ([\d\.]+)$")
LDD_MUSL_REGEX = re.compile(r"^musl libc .+$")

known_glibc_distros: Final[Mapping[float, str]] = {
    2.17: "centos7.6",
    2.27: "ubuntu18.04",
    2.28: "centos8.0",
    2.31: "ubuntu20.04",
    2.34: "centos9.0",
    2.35: "ubuntu22.04",
    2.39: "ubuntu24.04",
}


@dataclass
class ImageMetadataSpec:
    labels: Mapping[LabelName, str]
    digest: str
    canonical: str


class ImageMetadataSpecGenerator(ArgsSpecGenerator[ImageMetadataSpec]):
    pass


@dataclass
class ImageMetadataResult:
    runtime_type: str
    runtime_path: Optional[str]
    distro: str
    kernel_features: frozenset[KernelFeatures]


class ImageMetadataProvisioner(Provisioner[ImageMetadataSpec, ImageMetadataResult]):
    def __init__(self, valkey_stat_client: ValkeyStatClient) -> None:
        self._valkey_stat_client = valkey_stat_client

    @property
    @override
    def name(self) -> str:
        return "docker-image-metadata"

    @override
    async def setup(self, spec: ImageMetadataSpec) -> ImageMetadataResult:
        runtime_type, runtime_path = self._get_runtime_info(spec)
        kernel_features = self._get_kernel_features(spec)
        labeled_distro = self._get_distro_from_labels(spec)
        if labeled_distro is not None:
            return ImageMetadataResult(
                runtime_type,
                runtime_path,
                labeled_distro,
                kernel_features,
            )

        image_id = self._get_image_id(spec)
        cached_distro = await self._get_cached_distro(image_id)
        if cached_distro is not None:
            return ImageMetadataResult(
                runtime_type,
                runtime_path,
                cached_distro,
                kernel_features,
            )

        distro = await self._get_distro_from_container(spec)
        await self._set_distro_cache(image_id, distro)
        return ImageMetadataResult(runtime_type, runtime_path, distro, kernel_features)

    def _get_runtime_info(self, spec: ImageMetadataSpec) -> tuple[str, Optional[str]]:
        """
        Extracts runtime type and path from the provided labels.
        """
        runtime_type = spec.labels.get(LabelName.RUNTIME_TYPE, "app")
        runtime_path = spec.labels.get(LabelName.RUNTIME_PATH)
        return runtime_type, runtime_path

    def _get_kernel_features(self, spec: ImageMetadataSpec) -> frozenset[KernelFeatures]:
        """
        Extracts kernel features from the provided labels.
        """
        raw_features = spec.labels.get(LabelName.FEATURES, DEFAULT_KERNEL_FEATURE).split()
        features = [KernelFeatures(feature) for feature in raw_features]
        return frozenset(features)

    def _get_distro_from_labels(self, spec: ImageMetadataSpec) -> Optional[str]:
        """
        Extracts the distro from the provided labels.
        """
        return spec.labels.get(LabelName.BASE_DISTRO)

    def _get_image_id(self, spec: ImageMetadataSpec) -> str:
        """
        Extracts the image ID from the digest.
        """
        _, _, image_id = spec.digest.partition(":")
        return image_id

    async def _get_cached_distro(self, image_id: str) -> Optional[str]:
        """
        Retrieves the cached distro.
        """
        cached_distro = await self._valkey_stat_client.get_image_distro(image_id)
        return cached_distro

    async def _set_distro_cache(self, image_id: str, distro: str) -> None:
        """
        Caches the distro for the given image ID.
        """
        await self._valkey_stat_client.set_image_distro(image_id, distro)

    async def _get_distro_from_container(self, spec: ImageMetadataSpec) -> str:
        """
        Creates a temporary container to determine the distro.
        """
        async with Docker() as docker:
            container_config: dict[str, Any] = {
                "Image": spec.canonical,
                "Tty": True,
                "Privileged": False,
                "AttachStdin": False,
                "AttachStdout": True,
                "AttachStderr": True,
                "HostConfig": {
                    "Init": True,
                },
                "Entrypoint": [""],
                "Cmd": ["ldd", "--version"],
            }

            container = await docker.containers.create(container_config)
            await container.start()
            await container.wait()  # wait until container finishes to prevent race condition
            container_log = await container.log(stdout=True, stderr=True, follow=False)
            await container.stop()
            await container.delete()
            version_lines = container_log[0].splitlines()
            if m := LDD_GLIBC_REGEX.search(version_lines[0]):
                version = float(m.group(1))
                if version in known_glibc_distros:
                    distro = known_glibc_distros[version]
                else:
                    for idx, known_version in enumerate(known_glibc_distros.keys()):
                        if version < known_version:
                            distro = list(known_glibc_distros.values())[idx - 1]
                            break
                    else:
                        distro = list(known_glibc_distros.values())[-1]
            elif m := LDD_MUSL_REGEX.search(version_lines[0]):
                distro = "alpine3.8"
            else:
                raise RuntimeError("Could not determine the C library variant.")
        return distro

    @override
    async def teardown(self, resource: ImageMetadataResult) -> None:
        pass


class ImageMetadataStage(ProvisionStage[ImageMetadataSpec, ImageMetadataResult]):
    pass
