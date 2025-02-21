import asyncio
from typing import AsyncIterator, Dict, Final, Optional

from attr import dataclass
from raftify import RaftNode

from ai.backend.manager.raft.state_machine import HashStore, SetCommand


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
        self,
        raft_node: RaftNode,
        endpoints: list[str],
        connect_options: Optional["ConnectOptions"] = None,
    ) -> None:
        self.raft_node = raft_node
        self.endpoints = endpoints
        self.connect_options = connect_options

        self._state_machine = HashStore()
        self.communicator: RaftKVSCommunicator = RaftKVSCommunicator(self._state_machine)
        self._lock_store: Dict[bytes, asyncio.Lock] = {}
        self._watchers: Dict[bytes, asyncio.Queue] = {}
        self._leases: Dict[bytes, float] = {}  # Stores TTL expiration timestamps
        self._data_store: Dict[bytes, bytes] = {}  # KVS storage

    async def is_leader(self) -> bool:
        return await self.raft_node.is_leader()

    async def put(self, key: bytes, value: bytes) -> None:
        if not await self.is_leader():
            raise RuntimeError("Writes can only be performed on the Raft leader.")
        message = SetCommand(key.decode(), value.decode()).encode()
        await self.raft_node.propose(message)
        await self.notify_watchers(key, value)

    async def get(self, key: bytes) -> Optional[bytes]:
        state_machine = await self.raft_node.state_machine()
        assert isinstance(state_machine, HashStore)
        result = state_machine.get(key.decode())
        return result.encode() if result is not None else None

    async def delete(self, key: bytes) -> None:
        if not await self.is_leader():
            raise RuntimeError("Deletes can only be performed on the Raft leader.")
        message = SetCommand(key.decode(), "").encode()
        await self.raft_node.propose(message)
        await self.notify_watchers(key, None)

    async def get_cluster_size(self) -> int:
        return await self.raft_node.get_cluster_size()

    async def watch(self, key: bytes) -> asyncio.Queue:
        if key not in self._watchers:
            self._watchers[key] = asyncio.Queue()
        return self._watchers[key]

    async def notify_watchers(self, key: bytes, value: Optional[bytes]) -> None:
        if key in self._watchers:
            await self._watchers[key].put(value)

    async def lease_grant(self, key: bytes, ttl: int) -> None:
        self._leases[key] = asyncio.get_event_loop().time() + ttl

    async def lease_revoke(self, key: bytes) -> None:
        if key in self._leases:
            del self._leases[key]
            await self.delete(key)

    async def _cleanup_expired_leases(self) -> None:
        while True:
            now = asyncio.get_event_loop().time()
            expired_keys = [key for key, expiry in self._leases.items() if expiry < now]
            for key in expired_keys:
                await self.delete(key)
                del self._leases[key]
            await asyncio.sleep(1)  # Runs every second

    def connect(self, connect_options: Optional["ConnectOptions"] = None) -> "RaftKVSClient":
        return self

    async def with_lock(
        self, lock_options: RaftKVSLockOptions, connect_options: Optional["ConnectOptions"] = None
    ) -> "RaftKVSClient":
        lock = RaftKVSLock(self, lock_options, connect_options)
        await lock.__aenter__()
        self._current_lock = lock
        return self

    async def add_peer(self, id: int, addr: str) -> None:
        await self.raft_node.add_peer(id, addr)

    async def join_cluster(self, tickets: list) -> None:
        await self.raft_node.join_cluster(tickets)

    async def __aenter__(self) -> "RaftKVSCommunicator":
        asyncio.create_task(self._cleanup_expired_leases())
        return self.communicator

    async def __aexit__(self, *args) -> None:
        self._lock_store.clear()
        self._watchers.clear()
        self._leases.clear()


class RaftKVSLock:
    def __init__(
        self,
        client: RaftKVSClient,
        lock_options: RaftKVSLockOptions,
        connect_options: Optional["ConnectOptions"] = None,
    ) -> None:
        self.client = client
        self.lock_options = lock_options
        self.lock_acquired = False

    async def __aenter__(self) -> None:
        if not await self.client.is_leader():
            raise RuntimeError("Locks can only be acquired by the Raft leader.")

        lock_command = SetCommand(self.lock_options.lock_name.decode(), "LOCKED").encode()

        await self.client.raft_node.propose(lock_command)
        self.lock_acquired = True

    async def __aexit__(self, *args) -> None:
        if not self.lock_acquired:
            return

        unlock_command = SetCommand(self.lock_options.lock_name.decode(), "UNLOCKED").encode()

        await self.client.raft_node.propose(unlock_command)
        self.lock_acquired = False


class RaftKVSCommunicator:
    def __init__(self, state_machine: HashStore) -> None:
        self.state_machine = state_machine

    async def get(self, key: bytes) -> Optional[bytes]:
        result = self.state_machine.get(key.decode())
        return result.encode() if result is not None else None

    async def put(self, key: bytes, value: bytes) -> None:
        cmd = SetCommand(key.decode(), value.decode()).encode()
        await self.state_machine.apply(cmd)

    async def delete(self, key: bytes) -> None:
        cmd = SetCommand(key.decode(), "").encode()
        await self.state_machine.apply(cmd)


class Watch:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    async def __aiter__(self) -> AsyncIterator[Optional[bytes]]:
        while True:
            yield await self.queue.get()


class WatchEvent:
    key: bytes
    value: bytes
    event: "WatchEventType"
    prev_value: Optional[bytes]

    def __init__(
        self,
        key: bytes,
        value: bytes,
        event: "WatchEventType",
        prev_value: Optional[bytes] = None,
    ) -> None:
        self.key = key
        self.value = value
        self.event = event
        self.prev_value = prev_value


class WatchEventType:
    PUT: Final[str] = "PUT"
    DELETE: Final[str] = "DELETE"


class CondVar:
    """ """

    def __init__(self) -> None:
        """ """

    async def wait(self) -> None:
        """ """

    async def notify_waiters(self) -> None:
        """ """
