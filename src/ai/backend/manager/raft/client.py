import asyncio
import logging
from pathlib import Path
from typing import Optional

from raftify import Config as RaftConfig
from raftify import InitialRole, Peer, Peers, Raft
from raftify import RaftConfig as RaftCoreConfig

from ai.backend.common.config import read_from_file
from ai.backend.common.exception import ConfigurationError
from ai.backend.manager.raft.logger import Logger as RaftLogger
from ai.backend.manager.raft.state_machine import RaftHashStore
from ai.backend.manager.raft.utils import WebServer


class RaftKVSClient:
    def __init__(
        self,
        endpoints: list[str],
        raft_kvs_config_path: Optional[Path] = None,
    ):
        self.base_port = endpoints[0].split(":")[1]
        self.raft_nodes = {}
        self.leader_addr = None
        self.raft_instances = []

        raft_configs = self._load_cluster_config(raft_kvs_config_path)
        assert raft_configs is not None, "Raft configuration missing in manager.toml"

        raft_cluster_configs = raft_configs["raft-kvs"]

        other_peers = [
            {**peer, "myself": False} for peer in raft_cluster_configs["raft-kvs-peers"]["other"]
        ]
        my_peers = [
            {**peer, "myself": True} for peer in raft_cluster_configs["raft-kvs-peers"]["myself"]
        ]
        self.all_peers = sorted([*other_peers, *my_peers], key=lambda x: x["node_id"])

        initial_peers = Peers({
            int(peer_config["node-id"]): Peer(
                addr=f"{peer_config['host']}:{peer_config['port']}",
                role=InitialRole.from_str(peer_config["role"]),
            )
            for peer_config in self.all_peers
        })

        raft_core_config = RaftCoreConfig(
            heartbeat_tick=raft_configs["heartbeat-tick"],
            election_tick=raft_configs["election-tick"],
            min_election_tick=raft_configs["min-election-tick"],
            max_election_tick=raft_configs["max-election-tick"],
            max_committed_size_per_ready=raft_configs["max-committed-size-per-ready"],
            max_size_per_msg=raft_configs["max-size-per-msg"],
            max_inflight_msgs=raft_configs["max-inflight-msgs"],
            check_quorum=raft_configs["check-quorum"],
            batch_append=raft_configs["batch-append"],
            max_uncommitted_size=raft_configs["max-uncommitted-size"],
            skip_bcast_commit=raft_configs["skip-bcast-commit"],
            pre_vote=raft_configs["pre-vote"],
            priority=raft_configs["priority"],
        )

        raft_cfg = RaftConfig(
            log_dir=raft_configs["log-dir"],
            save_compacted_logs=True,
            compacted_log_dir=raft_configs["log-dir"],
            restore_wal_from=raft_cluster_configs["restore-wal-from"],
            restore_wal_snapshot_from=raft_cluster_configs["restore-wal-snapshot-from"],
            initial_peers=initial_peers,
            raft_config=raft_core_config,
        )

        # Extract `myself` node
        myself = next((peer for peer in my_peers), None)
        assert myself is not None, "Error: This node is not listed under `peers.myself`."
        node_id = myself["node-id"]

        raft_addr = initial_peers.get(node_id).get_addr()

        raft_logger = RaftLogger(
            logging.getLogger(f"{__spec__.name}.raft.node-{node_id}"),  # type: ignore
        )

        store = RaftHashStore()

        self.raft = Raft.bootstrap(
            node_id,
            raft_addr,
            store,  # type: ignore
            raft_cfg,
            raft_logger,  # type: ignore
        )
        self.raft.run()  # type: ignore

        if raft_cluster_configs["raft-debug-webserver-enabled"]:
            asyncio.create_task(
                WebServer(f"127.0.0.1:6025{node_id}", {"raft": self.raft, "store": store}).run()
            )

    def _load_cluster_config(
        self,
        raft_kvs_config_path: Optional[Path] = None,
    ) -> dict:
        try:
            raw_cfg, _ = read_from_file(raft_kvs_config_path, "raft-kvs")
        except ConfigurationError:
            raise Exception(f"Failed to load Raft KVS configuration from {raft_kvs_config_path}")

        return raw_cfg

    # async def put(self, key: str, value: str) -> None:
    #     """ Put a key-value pair into the Raft cluster. """
    #     leader_id = self.raft_node.get_id()
    #     if not self.raft_node.is_leader():
    #         leader_id = await self.raft_node.get_leader()

    #     client = RaftServiceClient(f"http://{self.leader_addr}")
    #     await client.put(key, value)
