import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, override

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


TSpec = TypeVar("TSpec")


class SpecGenerator(ABC, Generic[TSpec]):
    """
    Base class for all specs in the stage.

    This class is used to define the spec for the stage.
    When all fields in the spec is ready, provisioner can use the spec to setup the stage.
    """

    @abstractmethod
    async def wait_for_spec(self) -> TSpec:
        """
        Waits for the spec to be ready.
        """
        raise NotImplementedError


TResource = TypeVar("TResource")


class Provisioner(ABC, Generic[TSpec, TResource]):
    """
    Base class for all provisioners in the stage.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the provisioner.
        """
        raise NotImplementedError

    @abstractmethod
    async def setup(self, spec: TSpec) -> TResource:
        """
        Sets up the lifecycle stage.
        """
        raise NotImplementedError

    @abstractmethod
    async def teardown(self, resource: TResource) -> None:
        """
        Tears down the lifecycle stage.
        """
        raise NotImplementedError


class Stage(ABC, Generic[TSpec, TResource]):
    @abstractmethod
    async def setup(self, spec_generator: SpecGenerator[TSpec]) -> None:
        """
        Sets up the lifecycle stage.
        """
        raise NotImplementedError

    @abstractmethod
    async def wait_for_resource(self) -> TResource:
        """
        Waits for the resource to be ready.
        """
        raise NotImplementedError

    @abstractmethod
    async def teardown(self) -> None:
        """
        Tears down the lifecycle stage.
        """
        raise NotImplementedError


class ProvisionStage(Stage[TSpec, TResource]):
    """
    A stage that provisions a resource.

    This stage is used to provision a resource using a provisioner.
    It waits for the spec to be ready and then uses the provisioner to set up the resource.
    """

    _provisioner: Provisioner
    _resource: Optional[TResource]
    _setup_completed: asyncio.Event

    def __init__(self, provisioner: Provisioner):
        self._provisioner = provisioner
        self._resource = None
        self._setup_completed = asyncio.Event()

    async def setup(self, spec_generator: SpecGenerator[TSpec]) -> None:
        """
        Sets up the lifecycle stage.
        """
        spec = await spec_generator.wait_for_spec()
        try:
            resource = await self._provisioner.setup(spec)
            self._resource = resource
        except Exception as e:
            log.error("Failed to setup resource: %s", e)
        finally:
            self._setup_completed.set()

    async def wait_for_resource(self) -> TResource:
        await self._setup_completed.wait()
        if self._resource is None:
            raise RuntimeError("Resource setup failed")
        return self._resource

    async def teardown(self) -> None:
        """
        Tears down the lifecycle stage.
        """
        if self._resource is None:
            return
        await self._provisioner.teardown(self._resource)
        self._resource = None


class ArgsSpecGenerator(SpecGenerator[TSpec]):
    """
    A spec generator that uses the provided arguments as the spec.
    """

    _args: TSpec

    def __init__(self, args: TSpec):
        self._args = args

    @override
    async def wait_for_spec(self) -> TSpec:
        """
        Returns the provided arguments as the spec.
        """
        return self._args
