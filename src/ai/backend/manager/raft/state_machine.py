import pickle
from enum import Enum, StrEnum
from typing import Any, Optional, cast


class EventKind(Enum):
    """
    The kind of the event.
    """

    SET_KERNEL_STATE = "set_kernel_state"


class KernelStateType(StrEnum):
    """
    The type of the kernel event.
    """

    KernelPreparing = "kernel_preparing"
    KernelPulling = "kernel_pulling"
    KernelCreating = "kernel_creating"
    KernelStarted = "kernel_started"
    KernelCancelled = "kernel_cancelled"
    KernelTerminating = "kernel_terminating"
    KernelTerminated = "kernel_terminated"


class Event:
    """
    Use pickle to serialize the data.
    """

    def __init__(self, kind: EventKind, next_state: KernelStateType, arg: Any) -> None:
        self.kind = kind
        self.next_state = next_state
        self.arg = arg

    def encode(self) -> bytes:
        return pickle.dumps(self.__dict__)

    @classmethod
    def decode(cls, packed: bytes) -> "Event":
        unpacked = pickle.loads(packed)
        return cls(unpacked["kind"], unpacked["next_state"], unpacked["arg"])


def handle_kernel_state_transition(next_state: KernelStateType, arg: Any):
    match next_state:
        case KernelStateType.KernelPreparing:
            pass
        case KernelStateType.KernelPulling:
            pass
        case KernelStateType.KernelCreating:
            pass
        case KernelStateType.KernelStarted:
            pass
        case KernelStateType.KernelCancelled:
            pass
        case KernelStateType.KernelTerminating:
            pass
        case KernelStateType.KernelTerminated:
            pass


# TODO: Remove _store and replace it HashStore itself
class HashStore:
    """
    A simple key-value store that stores data in memory.
    Use pickle to serialize the data.
    """

    def __init__(self):
        # TODO: Replace RDB tables with these
        self._store = dict({
            "kernels": None,
            "sessions": None,
        })

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def get_kernel_row(self, kernel_id: str) -> Optional[str]:
        # TODO: Implement SQL query to raftify
        pass

    def apply(self, msg: bytes) -> bytes:
        event = Event.decode(msg)

        match event.kind:
            case EventKind.SET_KERNEL_STATE:
                handle_kernel_state_transition(cast(KernelStateType, event.next_state), event.arg)

        return msg

    def as_dict(self) -> dict:
        return self._store

    def snapshot(self) -> bytes:
        return pickle.dumps(self._store)

    def restore(self, snapshot: bytes) -> None:
        self._store = pickle.loads(snapshot)
