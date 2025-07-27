import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from ai.backend.common.docker import (
    ImageRef,
)
from ai.backend.common.types import (
    AgentId,
    ContainerId,
    ContainerStatus,
    ImageRegistry,
    KernelId,
    Sentinel,
)

from ..data.cgroup import CGroupInfo
from ..data.kernel.creator import KernelCreationInfo
from ..types import Container
from .defs import ACTIVE_STATUS_SET


class AbstractBackend(ABC):
    """
    Abstract base class for backend implementations.
    """

    @abstractmethod
    async def create_kernel(
        self,
        info: KernelCreationInfo,
        *,
        throttle_sema: Optional[asyncio.Semaphore] = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def create_local_network(self, network_name: str) -> None:
        """
        Create a local bridge network for a single-node multicontainer session, where containers in the
        same agent can connect to each other using cluster hostnames without explicit port mapping.

        This is called by the manager before kernel creation.
        It may raise :exc:`NotImplementedError` and then the manager
        will cancel creation of the session.
        """
        raise NotImplementedError

    @abstractmethod
    async def destroy_kernel(self, kernel_id: KernelId) -> None:
        raise NotImplementedError

    @abstractmethod
    async def destroy_local_network(self, network_name: str) -> None:
        """
        Destroy a local bridge network used for a single-node multi-container session.

        This is called by the manager after kernel destruction.
        """
        raise NotImplementedError

    @abstractmethod
    async def clean_kernel(self, kernel_id: KernelId) -> None:
        raise NotImplementedError

    @abstractmethod
    async def restart_kernel(self, kernel_id: KernelId) -> None:
        raise NotImplementedError

    @abstractmethod
    async def yield_temp_container(self, image: ImageRef) -> AsyncIterator[Container]:
        """
        Yield a temporary container from given image.
        This is used to run backend-specific tasks that require a container.
        The container should be cleaned up after use.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_container_logs(self, container_id: ContainerId) -> list[str]:
        """
        Get the logs of the container.
        This method should return a list of log lines as strings.
        """
        raise NotImplementedError

    # No need to implement this method
    # Should rather implement those methods in the backend:
    # - yield_temp_container()
    # - get_container_log()
    # And implement this method in the agent:
    # - get_distro_from_container_log()
    # @abstractmethod
    # async def resolve_image_distro(self, image: ImageConfig) -> str:
    #     """
    #     Resolve the image distribution for the given image configuration.
    #     This method should return the distribution name as a string.
    #     """
    #     raise NotImplementedError

    # No need to implement this method
    # Should rather implement those methods in the backend:
    # - get_managed_images()
    # Implement it in the agent:
    # -
    # @abstractmethod
    # async def scan_images(self) -> ScanImagesResult:
    #     """
    #     Scan the available kernel images/templates and update ``self.images``.
    #     This is called periodically to keep the image list up-to-date and allow
    #     manual image addition and deletions by admins.
    #     """

    @abstractmethod
    async def get_managed_images(self) -> tuple[ImageRef]:
        raise NotImplementedError

    @abstractmethod
    async def get_managed_containers(
        self,
        agent_id: Optional[AgentId] = None,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> tuple[Container]:
        """
        Get all containers managed by this backend.
        This method should return a tuple of Container objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_cgroup_info(self, container_id: ContainerId, controller: str) -> CGroupInfo:
        """
        Get the cgroup path for the given controller and container ID, and the cgroup version.
        This is used to read/write cgroup files for resource management.
        """
        raise NotImplementedError

    @abstractmethod
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        """
        Push the image.
        This method should be implemented by the backend to handle image pushing.
        """
        raise NotImplementedError

    @abstractmethod
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        """
        Pull the image.
        This method should be implemented by the backend to handle image pulling.
        """
        raise NotImplementedError
