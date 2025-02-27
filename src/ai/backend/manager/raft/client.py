import asyncio
from typing import AsyncIterator, Dict, Final, List, Optional, Self, Tuple

import aiohttp
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
    def with_user(self, user: str, password: str) -> Self:
        return self

    def with_keep_alive(self, interval: float, timeout: float) -> Self:
        return self

    def with_keep_alive_while_idle(self, enabled: bool) -> Self:
        return self

    def with_connect_timeout(self, connect_timeout: float) -> Self:
        return self

    def with_timeout(self, timeout: float) -> Self:
        return self

    def with_tcp_keepalive(self, tcp_keepalive: float) -> Self:
        return self


class WatchEventType:
    PUT: Final[str] = "PUT"
    DELETE: Final[str] = "DELETE"


class WatchEvent:
    key: bytes
    value: Optional[bytes]
    event_type: str
    prev_value: Optional[bytes]

    def __init__(
        self,
        key: bytes,
        value: Optional[bytes],
        event_type: str,
        revision: int,
        prev_value: Optional[bytes] = None,
    ) -> None:
        self.key = key
        self.value = value
        self.event_type = event_type
        self.revision = revision
        self.prev_value = prev_value


class Watch:
    def __init__(self, queue: asyncio.Queue[WatchEvent]) -> None:
        self.queue = queue

    def __aiter__(self) -> AsyncIterator[WatchEvent]:
        return self

    async def __anext__(self) -> WatchEvent:
        return await self.queue.get()


class RaftKVSClient:
    _raft_node: RaftNode
    _endpoints: list[str]
    _connect_options: Optional[ConnectOptions]
    _state_machine: HashStore
    # _communicator: "RaftKVSCommunicator"
    _watchers: Dict[bytes, list[asyncio.Queue[WatchEvent]]]
    _prefix_watchers: List[Tuple[bytes, asyncio.Queue[WatchEvent]]]
    _leases: Dict[bytes, float]
    _lease_task: Optional[asyncio.Task]
    _encoding: str

    def __init__(
        self,
        raft_node: RaftNode,
        endpoints: list[str],
        connect_options: Optional[ConnectOptions] = None,
    ) -> None:
        self._raft_node = raft_node
        self._endpoints = endpoints
        self._connect_options = connect_options

        self._state_machine = HashStore()
        # self._communicator: RaftKVSCommunicator = RaftKVSCommunicator(self._state_machine)
        self._watchers = {}
        self._prefix_watchers = []
        self._leases: Dict[bytes, float] = {}  # Stores TTL expiration timestamps
        self._lease_task: Optional[asyncio.Task] = None

    async def connect(self, connect_options: Optional["ConnectOptions"] = None) -> Self:
        if connect_options:
            self._connect_options = connect_options

        if not self._lease_task:
            self._lease_task = asyncio.create_task(self._cleanup_expired_leases())

        return self

    async def close(self) -> None:
        if self._lease_task:
            self._lease_task.cancel()
            self._lease_task = None

        self._watchers.clear()
        self._leases.clear()

    async def is_leader(self) -> bool:
        return await self._raft_node.is_leader()

    async def get_leader_id(self) -> Optional[int]:
        return await self._raft_node.get_leader_id()

    async def _get_leader_addr(self) -> Optional[str]:
        leader_id = await self.get_leader_id()
        if leader_id is None:
            return None

        for endpoint in self._endpoints:
            if endpoint.startswith(f"{leader_id}:"):
                return endpoint.split(":", 1)[1]
        return None

    async def _redirect_write_to_leader(self, key: bytes, value: bytes, method: str) -> None:
        leader_addr = await self._get_leader_addr()
        if leader_addr is None:
            raise RuntimeError("No leader found in the cluster. Request cannot be redirected.")

        if method == "PUT":
            url = f"http://{leader_addr}/put/{key.decode()}/{value.decode()}"
        elif method == "DELETE":
            url = f"http://{leader_addr}/delete/{key.decode()}"
        else:
            raise RuntimeError(f"Unsupported method: {method}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"Failed to redirect request to leader: {resp.status}")
        except Exception as e:
            raise RuntimeError(f"Failed to redirect request to leader: {e}")

    async def watch(self, key: bytes, start_revision: Optional[int] = None) -> Watch:
        if key not in self._watchers:
            self._watchers[key] = []
        queue: asyncio.Queue[WatchEvent] = asyncio.Queue()
        self._watchers[key].append(queue)
        return Watch(queue)

    async def watch_prefix(self, prefix: bytes, start_revision: Optional[int] = None) -> Watch:
        queue: asyncio.Queue[WatchEvent] = asyncio.Queue()
        self._prefix_watchers.append((prefix, queue))
        return Watch(queue)

    async def notify_watchers(
        self,
        key: bytes,
        event_type: str,
        new_value: Optional[bytes],
        revision: int,
        prev_value: Optional[bytes] = None,
    ) -> None:
        event = WatchEvent(key, new_value, event_type, revision, prev_value)

        if key in self._watchers:
            for queue in self._watchers[key]:
                await queue.put(event)

        for prefix, q in self._prefix_watchers:
            if key.startswith(prefix):
                await q.put(event)

    async def put(self, key: bytes, value: bytes) -> None:
        if not await self.is_leader():
            await self._redirect_write_to_leader(key, value, method="PUT")
            return
        # todo: add mutex
        message = SetCommand(key.decode(), value.decode()).encode()
        """
        for msg in message_list:
            match operation {
                case "PUT":
                    message = SetCommand(key.decode(), value.decode()).encode()
                case "DELETE":
                case _:
                    raise RuntimeError(f"Unsupported operation: {operation}")
            }
        """
        await self._raft_node.propose(message)
        # todo: end mutex
        revision = self._state_machine.current_revision()
        old_val = self._state_machine.get(key.decode())

        await self.notify_watchers(
            key,
            WatchEventType.PUT,
            value,
            revision,
            prev_value=old_val.encode() if old_val else None,
        )

    # todo implement multiple puts
    # message pre-processing needs to be synchronous?

    async def get(self, key: bytes) -> Optional[bytes]:
        # todo: check if data reads might be stale
        val = self._state_machine.get(key.decode())
        return val.encode() if val is not None else None

    async def delete(self, key: bytes) -> None:
        if not await self.is_leader():
            await self._redirect_write_to_leader(key, b"", method="DELETE")
            return

        old_val = self._state_machine.get(key.decode())
        message = SetCommand(key.decode(), "").encode()  # send empty value to delete
        await self._raft_node.propose(message)

        revision = self._state_machine.current_revision()
        if old_val is not None:
            await self.notify_watchers(
                key, WatchEventType.DELETE, None, revision, prev_value=old_val.encode()
            )

    # todo implement multiple deletes

    async def get_cluster_size(self) -> int:
        return await self._raft_node.get_cluster_size()

    async def lease_grant(self, key: bytes, ttl: int) -> None:
        if not await self.is_leader():
            await self._redirect_write_to_leader(key, str(ttl).encode(), method="PUT")
            return

        self._leases[key] = asyncio.get_event_loop().time() + ttl

    async def lease_revoke(self, key: bytes) -> None:
        if key not in self._leases:
            return

        if not await self.is_leader():
            await self._redirect_write_to_leader(key, b"", method="DELETE")
            return

        del self._leases[key]
        await self.delete(key)

    async def _cleanup_expired_leases(self) -> None:
        try:
            while True:
                await asyncio.sleep(1)
                if not await self.is_leader():
                    continue

                now = asyncio.get_event_loop().time()
                expired = [k for k, exp in self._leases.items() if exp < now]
                for key in expired:
                    await self.lease_revoke(key)
        except asyncio.CancelledError:
            pass

    async def with_lock(
        self, lock_options: RaftKVSLockOptions, connect_options: Optional["ConnectOptions"] = None
    ) -> Self:
        if not await self.is_leader():
            raise RuntimeError("Locks can only be acquired by the Raft leader.")

        message = SetCommand(lock_options.lock_name.decode(), "LOCKED").encode()
        await self._raft_node.propose(message)

        return self

    async def add_peer(self, id: int, addr: str) -> None:
        if not await self.is_leader():
            raise RuntimeError("Only the leader can add peers to the cluster.")

        await self._raft_node.add_peer(id, addr)

    async def join_cluster(self, tickets: list) -> None:
        await self._raft_node.join_cluster(tickets)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()


# class RaftKVSCommunicator:
#     def __init__(self, state_machine: HashStore) -> None:
#         self.state_machine = state_machine
#         self._watchers: Dict[bytes, List[asyncio.Queue[WatchEvent]]] = {}


#     async def get(self, key: bytes) -> Optional[bytes]:
#         result = self.state_machine.get(key.decode())
#         return result.encode() if result is not None else None

#     async def put(self, key: bytes, value: bytes) -> None:
#         cmd = SetCommand(key.decode(), value.decode()).encode()
#         await self.state_machine.apply(cmd)

#     async def delete(self, key: bytes) -> None:
#         cmd = SetCommand(key.decode(), "").encode()
#         await self.state_machine.apply(cmd)

#     async def watch(self, key: bytes, start_revision: Optional[int] = None) -> Watch:
#         if key not in self._watchers:
#             self._watchers[key] = []
#         queue: asyncio.Queue[WatchEvent] = asyncio.Queue()
#         self._watchers[key].append(queue)
#         return Watch(queue)

#     async def watch_prefix(self, prefix: bytes, start_revision: Optional[int] = None) -> Watch:
#         queue: asyncio.Queue[WatchEvent] = asyncio.Queue()
#         self._watchers.setdefault(prefix, []).append(queue)
#         return Watch(queue)


# class CondVar:
#     """ """

#     def __init__(self) -> None:
#         """ """

#     async def wait(self) -> None:
#         """ """

#     async def notify_waiters(self) -> None:
#         """ """
