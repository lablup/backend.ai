import pickle
from typing import Any

from aiohttp import web
from aiohttp.web import RouteTableDef
from raftify import (
    Raft,
    set_confchange_context_deserializer,
    set_confchangev2_context_deserializer,
    set_entry_context_deserializer,
    set_entry_data_deserializer,
    set_fsm_deserializer,
    set_log_entry_deserializer,
    set_message_context_deserializer,
    set_snapshot_data_deserializer,
)

from ai.backend.manager.raft.state_machine import HashStore

routes = RouteTableDef()
"""
APIs of the web servers to interact with the RaftServers.
"""


@routes.get("/get/{id}")
async def get(request: web.Request) -> web.Response:
    store: HashStore = request.app["state"]["store"]
    id = request.match_info["id"]
    return web.Response(text=store.get(id))


@routes.get("/leader")
async def leader(request: web.Request) -> web.Response:
    raft: Raft = request.app["state"]["raft"]
    leader_id = str(await raft.get_raft_node().get_leader_id())
    return web.Response(text=leader_id)


@routes.get("/size")
async def size(request: web.Request) -> web.Response:
    raft: Raft = request.app["state"]["raft"]
    size = str(await raft.get_raft_node().get_cluster_size())
    return web.Response(text=size)


@routes.get("/leave_joint")
async def leave_joint(request: web.Request) -> web.Response:
    raft: Raft = request.app["state"]["raft"]
    await raft.get_raft_node().leave_joint()
    return web.Response(text="OK")


# @routes.get("/put/{id}/{value}")
# async def put(request: web.Request) -> web.Response:
#     raft: Raft = request.app["state"]["raft"]
#     id, value = request.match_info["id"], request.match_info["value"]
#     message = SetCommand(id, value)

#     await raft.get_raft_node().propose(message.encode())
#     return web.Response(text="OK")


class WebServer:
    """
    Simple webserver for Raft cluster testing.
    Do not use this class for anything other than testing purposes.
    """

    def __init__(self, addr: str, state: dict[str, Any]):
        self.app = web.Application()
        self.app.add_routes(routes)
        self.app["state"] = state
        self.host, self.port = addr.split(":")
        self.runner = None

    async def run(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()


def pickle_deserialize(data: bytes) -> str | None:
    if data == b"":
        return None

    if pickle.PROTO in data:
        r = pickle.loads(data[data.index(pickle.PROTO) :])
        return r

    # Not pickle data
    return None


def register_custom_deserializer() -> None:
    """
    Initialize the custom deserializers.
    """

    set_confchange_context_deserializer(pickle_deserialize)
    set_confchangev2_context_deserializer(pickle_deserialize)
    set_entry_context_deserializer(pickle_deserialize)
    set_entry_data_deserializer(pickle_deserialize)
    set_message_context_deserializer(pickle_deserialize)
    set_snapshot_data_deserializer(pickle_deserialize)
    set_log_entry_deserializer(pickle_deserialize)
    set_fsm_deserializer(pickle_deserialize)
