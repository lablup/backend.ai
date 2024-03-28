from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from ..common.types import DeviceId, SlotName


class InitializationError(Exception):
    """
    Errors during agent initialization and compute plugin setup
    """

    pass


class ResourceError(ValueError):
    pass


class InvalidArgumentError(RuntimeError):
    pass


class UnsupportedResource(ResourceError):
    pass


class InvalidResourceCombination(ResourceError):
    pass


class InvalidResourceArgument(ResourceError):
    pass


class NotMultipleOfQuantum(InvalidResourceArgument):
    pass


@dataclass
class InsufficientResource(ResourceError):
    msg: str
    slot_name: SlotName
    requested_alloc: Decimal
    total_allocatable: Decimal | int
    allocation: dict[SlotName, dict[DeviceId, Decimal]]
    context_tag: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"InsufficientResource: {self.msg} ({self.slot_name}"
            + (f" (tag: {self.context_tag!r}), " if self.context_tag else ", ")
            + f"allocating {self.requested_alloc} out of {self.total_allocatable})"
        )

    def __reduce__(self):
        return (
            self.__class__,
            (
                self.msg,
                self.slot_name,
                self.requested_alloc,
                self.total_allocatable,
                self.allocation,
                self.context_tag,
            ),
        )


class UnsupportedBaseDistroError(RuntimeError):
    pass


class ContainerCreationError(Exception):
    container_id: str

    def __init__(self, container_id: str, message: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container_id = container_id
        self.message = message


class K8sError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class AgentError(RuntimeError):
    """
    A dummy exception class to distinguish agent-side errors passed via
    aiozmq.rpc calls.

    It carrise two args tuple: the exception type and exception arguments from
    the agent.
    """

    def __init__(self, *args, exc_repr: str = None):
        super().__init__(*args)
        self.exc_repr = exc_repr
