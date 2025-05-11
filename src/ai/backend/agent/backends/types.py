from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Mapping

from ai.backend.agent.resources import AbstractComputePlugin
from ai.backend.common.types import CIStrEnum, DeviceName, SlotName


class BackendType(CIStrEnum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DUMMY = "dummy"


class AbstractBackend(ABC):
    @abstractmethod
    async def load_resources(
        self,
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        """
        Detect available resources attached on the system and load corresponding device plugin.
        """

    @abstractmethod
    async def scan_available_resources(
        self,
    ) -> Mapping[SlotName, Decimal]:
        """
        Scan and define the amount of available resource slots in this node.
        """

    @abstractmethod
    async def create_local_network(self, network_name: str) -> None:
        """
        Create a local bridge network for a single-node multicontainer session, where containers in the
        same agent can connect to each other using cluster hostnames without explicit port mapping.

        This is called by the manager before kernel creation.
        It may raise :exc:`NotImplementedError` and then the manager
        will cancel creation of the session.
        """

    @abstractmethod
    async def destroy_local_network(self, network_name: str) -> None:
        """
        Destroy a local bridge network used for a single-node multi-container session.

        This is called by the manager after kernel destruction.
        """
