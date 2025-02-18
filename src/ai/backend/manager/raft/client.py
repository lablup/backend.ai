from typing import Optional

from attr import dataclass


@dataclass
class RaftKVSLockOptions:
    lock_name: bytes
    timeout: Optional[float]
    ttl: Optional[int]


class ConnectOptions:
    def __init__(self) -> None: ...
    def with_user(self, user: str, password: str) -> "ConnectOptions":
        return self

    def with_keep_alive(self, interval: float, timeout: float) -> "ConnectOptions":
        return self

    def with_keep_alive_while_idle(self, enabled: bool) -> "ConnectOptions":
        return self

    def with_connect_timeout(self, connect_timeout: float) -> "ConnectOptions":
        return self

    def with_timeout(self, timeout: float) -> "ConnectOptions":
        return self

    def with_tcp_keepalive(self, tcp_keepalive: float) -> "ConnectOptions":
        return self


class RaftKVSClient:
    def __init__(
        self, endpoints: list[str], connect_options: Optional["ConnectOptions"] = None
    ) -> None:
        self.endpoints = endpoints
        self.connect_options = connect_options
        self.communicator: Optional[RaftKVSCommunicator] = RaftKVSCommunicator()

    def connect(self, connect_options: Optional["ConnectOptions"] = None) -> "RaftKVSClient":
        """ """
        return self

    def with_lock(
        self,
        lock_options: "RaftKVSLockOptions",
        connect_options: Optional["ConnectOptions"] = None,
    ) -> "RaftKVSClient":
        if self.communicator is None:
            raise RuntimeError(
                "Cannot create lock: Client is not connected. Use 'async with RaftKVSClient()' first."
            )
        return self

    async def __aenter__(self) -> "RaftKVSCommunicator":
        self.communicator = RaftKVSCommunicator()
        return self.communicator

    async def __aexit__(self, *args) -> None:
        self.communicator = None


class RaftKVSLock:
    def __init__(self, client: RaftKVSClient, lock_options: RaftKVSLockOptions) -> None:
        self.client = client
        self.lock_options = lock_options
        self.lock_acquired = False

    async def __aenter__(self) -> "RaftKVSCommunicator":
        """Acquire the lock and return the communicator."""
        self.lock_acquired = True

        if not hasattr(self.client, "communicator") or self.client.communicator is None:
            self.client.communicator = (
                RaftKVSCommunicator()
            )  # ✅ Ensure a communicator always exists

        return self.client.communicator  # ✅ Always returns a valid communicator

    async def __aexit__(self, *args) -> None:
        """Release the lock."""
        self.lock_acquired = False


class RaftKVSCommunicator:
    pass
    # async def get(self, key: bytes) -> list[int]:
    #     """
    #     Gets the key from the key-value store.
    #     """
    #     return list(self.store.get(key, []))
    # async def get_prefix(self, key: bytes) -> list[tuple[list[int], list[int]]]:
    #     """
    #     Gets the key from the key-value store.
    #     """
    #     return [(key, [])]
    # async def put(self, key: bytes, value: bytes) -> None:
    #     """
    #     Put the given key into the key-value store.
    #     A put request increments the revision of the key-value store
    #     and generates one event in the event history.
    #     """
    # async def txn(self, txn: "Txn") -> "TxnResponse":
    #     """
    #     Processes multiple operations in a single transaction.
    #     A txn request increments the revision of the key-value store
    #     and generates events with the same revision for every completed operation.
    #     It is not allowed to modify the same key several times within one txn.
    #     """
    # async def delete(self, key: bytes) -> None:
    #     """
    #     Deletes the given key from the key-value store.
    #     """
    # async def delete_prefix(self, key: bytes) -> None:
    #     """
    #     Deletes the given key from the key-value store.
    #     """
    # async def keys_prefix(self, key: bytes) -> list[list[int]]:
    #     """ """
    # async def lock(self, name: bytes) -> None:
    #     """
    #     Lock acquires a distributed shared lock on a given named lock.
    #     On success, it will return a unique key that exists so long as the
    #     lock is held by the caller. This key can be used in conjunction with
    #     transactions to safely ensure updates to etcd only occur while holding
    #     lock ownership. The lock is held until Unlock is called on the key or the
    #     lease associate with the owner expires.
    #     """
    # async def unlock(self, name: bytes) -> None:
    #     """
    #     Unlock takes a key returned by Lock and releases the hold on lock. The
    #     next Lock caller waiting for the lock will then be woken up and given
    #     ownership of the lock.
    #     """
    # async def lease_grant(self, ttl: int) -> None:
    #     """
    #     Creates a lease which expires if the server does not receive a keepAlive
    #     within a given time to live period. All keys attached to the lease will be expired and
    #     deleted if the lease expires. Each expired key generates a delete event in the event history.
    #     """
    # async def lease_revoke(self, id: int) -> None:
    #     """Revokes a lease. All keys attached to the lease will expire and be deleted."""
    # async def lease_time_to_live(self, id: int) -> None:
    #     """Retrieves lease information."""
    # async def lease_keep_alive(self, id: int) -> None:
    #     """
    #     Keeps the lease alive by streaming keep alive requests from the client
    #     to the server and streaming keep alive responses from the server to the client.
    #     """
    # def watch(
    #     self,
    #     key: bytes,
    #     *,
    #     once: Optional[bool] = False,
    #     ready_event: Optional["CondVar"] = None,
    # ) -> "Watch":
    #     """
    #     Watches for events happening or that have happened. Both input and output
    #     are streams; the input stream is for creating and canceling watcher and the output
    #     stream sends events. The entire event history can be watched starting from the
    #     last compaction revision.
    #     """
    #     while True:
    #         yield WatchEvent(b"", b"", WatchEventType.PUT)
    # def watch_prefix(
    #     self,
    #     key: bytes,
    #     *,
    #     once: Optional[bool] = False,
    #     ready_event: Optional["CondVar"] = None,
    # ) -> "Watch":
    #     """
    #     Watches for events happening or that have happened. Both input and output
    #     are streams; the input stream is for creating and canceling watcher and the output
    #     stream sends events. The entire event history can be watched starting from the
    #     last compaction revision.
    #     """


# class Watch:
#     """ """

#     async def __aiter__(self) -> AsyncIterator["Watch"]:
#         """ """
#     async def __anext__(self) -> "WatchEvent":
#         """ """

# class WatchEvent:
#     key: bytes
#     value: bytes
#     event: "WatchEventType"
#     prev_value: Optional[bytes]

#     def __init__(
#         self,
#         key: bytes,
#         value: bytes,
#         event: "WatchEventType",
#         prev_value: Optional[bytes] = None,
#     ) -> None:
#         self.key = key
#         self.value = value
#         self.event = event
#         self.prev_value = prev_value

# class WatchEventType:
#     """ """

#     PUT: Final[Any]
#     """
#     """
#     DELETE: Final[Any]
#     """
#     """

# class CondVar:
#     """ """

#     def __init__(self) -> None:
#         """ """
#     async def wait(self) -> None:
#         """ """
#     async def notify_waiters(self) -> None:
#         """ """
