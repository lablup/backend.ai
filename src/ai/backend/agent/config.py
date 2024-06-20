import os

import trafaret as t

from ai.backend.common import config
from ai.backend.common import validators as tx

from .affinity_map import AffinityPolicy
from .stats import StatModes
from .types import AgentBackend

coredump_defaults = {
    "enabled": False,
    "path": "./coredumps",
    "backup-count": 10,
    "size-limit": "64M",
}

agent_local_config_iv = (
    t.Dict({
        t.Key("agent"): t.Dict({
            tx.AliasedKey(["backend", "mode"]): tx.Enum(AgentBackend),
            t.Key("rpc-listen-addr", default=("", 6001)): tx.HostPortPair(allow_blank_host=True),
            t.Key("advertised-rpc-addr", default=None): t.Null | tx.HostPortPair,
            t.Key("rpc-auth-manager-public-key", default=None): t.Null | tx.Path(type="file"),
            t.Key("rpc-auth-agent-keypair", default=None): t.Null | tx.Path(type="file"),
            t.Key("agent-sock-port", default=6007): t.ToInt[1024:65535],
            t.Key("id", default=None): t.Null | t.String,
            t.Key("ipc-base-path", default="/tmp/backend.ai/ipc"): tx.Path(
                type="dir", auto_create=True
            ),
            t.Key("var-base-path", default="./var/lib/backend.ai"): tx.Path(
                type="dir", auto_create=True
            ),
            t.Key("mount-path", default=None): t.Null | tx.Path(type="dir", auto_create=True),
            t.Key("cohabiting-storage-proxy", default=True): t.Bool(),
            t.Key("public-host", default=None): t.Null | t.String,
            t.Key("region", default=None): t.Null | t.String,
            t.Key("instance-type", default=None): t.Null | t.String,
            t.Key("scaling-group", default="default"): t.String,
            t.Key("pid-file", default=os.devnull): tx.Path(
                type="file", allow_nonexisting=True, allow_devnull=True
            ),
            t.Key("event-loop", default="asyncio"): t.Enum("asyncio", "uvloop"),
            t.Key("skip-manager-detection", default=False): t.ToBool,
            tx.AliasedKey(["aiomonitor-termui-port", "aiomonitor-port"], default=48200): t.ToInt[
                1:65535
            ],
            t.Key("aiomonitor-webui-port", default=49200): t.ToInt[1:65535],
            t.Key("metadata-server-bind-host", default="0.0.0.0"): t.String,
            t.Key("metadata-server-port", default=40128): t.ToInt[1:65535],
            t.Key("allow-compute-plugins", default=None): t.Null | tx.ToSet,
            t.Key("block-compute-plugins", default=None): t.Null | tx.ToSet,
            t.Key("image-commit-path", default="./tmp/backend.ai/commit"): tx.Path(
                type="dir", auto_create=True
            ),
            t.Key("abuse-report-path", default=None): t.Null
            | tx.Path(type="dir", allow_nonexisting=True),
            t.Key("force-terminate-abusing-containers", default=False): t.ToBool,
            t.Key("kernel-creation-concurrency", default=4): t.ToInt[1:32],
            t.Key("use-experimental-redis-event-dispatcher", default=False): t.ToBool,
        }).allow_extra("*"),
        t.Key("container"): t.Dict({
            t.Key("kernel-uid", default=-1): tx.UserID,
            t.Key("kernel-gid", default=-1): tx.GroupID,
            t.Key("bind-host", default=""): t.String(allow_blank=True),
            t.Key("advertised-host", default=None): t.Null | t.String(),
            t.Key("port-range", default=(30000, 31000)): tx.PortRange,
            t.Key("stats-type", default="docker"): t.Null | t.Enum(*[e.value for e in StatModes]),
            t.Key("sandbox-type", default="docker"): t.Enum("docker", "jail"),
            t.Key("jail-args", default=[]): t.List(t.String),
            t.Key("scratch-type"): t.Enum("hostdir", "hostfile", "memory", "k8s-nfs"),
            t.Key("scratch-root", default="./scratches"): tx.Path(type="dir", auto_create=True),
            t.Key("scratch-size", default="0"): tx.BinarySize,
            t.Key("scratch-nfs-address", default=None): t.Null | t.String,
            t.Key("scratch-nfs-options", default=None): t.Null | t.String,
            t.Key("alternative-bridge", default=None): t.Null | t.String,
        }).allow_extra("*"),
        t.Key("logging"): t.Any,  # checked in ai.backend.common.logging
        t.Key("resource"): t.Dict({
            t.Key("reserved-cpu", default=1): t.Int,
            t.Key("reserved-mem", default="1G"): tx.BinarySize,
            t.Key("reserved-disk", default="8G"): tx.BinarySize,
            t.Key("allocation-order", default=["cuda", "rocm", "tpu", "cpu", "mem"]): t.List(
                t.String
            ),
            t.Key("affinity-policy", default=AffinityPolicy.INTERLEAVED.name): tx.Enum(
                AffinityPolicy,
                use_name=True,
            ),
        }).allow_extra("*"),
        t.Key("debug"): t.Dict({
            t.Key("enabled", default=False): t.ToBool,
            t.Key("asyncio", default=False): t.ToBool,
            t.Key("kernel-runner", default=False): t.ToBool,
            t.Key("enhanced-aiomonitor-task-info", default=False): t.ToBool,
            t.Key("skip-container-deletion", default=False): t.ToBool,
            t.Key("log-stats", default=False): t.ToBool,
            t.Key("log-kernel-config", default=False): t.ToBool,
            t.Key("log-alloc-map", default=False): t.ToBool,
            t.Key("log-events", default=False): t.ToBool,
            t.Key("log-heartbeats", default=False): t.ToBool,
            t.Key("heartbeat-interval", default=20.0): t.Float,
            t.Key("log-docker-events", default=False): t.ToBool,
            t.Key("coredump", default=coredump_defaults): t.Dict({
                t.Key("enabled", default=coredump_defaults["enabled"]): t.ToBool,
                t.Key("path", default=coredump_defaults["path"]): tx.Path(
                    type="dir", auto_create=True
                ),
                t.Key("backup-count", default=coredump_defaults["backup-count"]): t.Int[1:],
                t.Key("size-limit", default=coredump_defaults["size-limit"]): tx.BinarySize,
            }).allow_extra("*"),
        }).allow_extra("*"),
    })
    .merge(config.etcd_config_iv)
    .allow_extra("*")
)

docker_extra_config_iv = t.Dict({
    t.Key("container"): t.Dict({
        t.Key("swarm-enabled", default=False): t.ToBool,
    }).allow_extra("*"),
}).allow_extra("*")

default_container_logs_config = {
    "max-length": "10M",  # the maximum tail size
    "chunk-size": "64K",  # used when storing logs to Redis as a side-channel to the event bus
}

agent_etcd_config_iv = t.Dict({
    t.Key("container-logs", default=default_container_logs_config): t.Dict({
        t.Key("max-length", default=default_container_logs_config["max-length"]): tx.BinarySize(),
        t.Key("chunk-size", default=default_container_logs_config["chunk-size"]): tx.BinarySize(),
    }).allow_extra("*"),
}).allow_extra("*")

container_etcd_config_iv = t.Dict({
    t.Key("kernel-uid", optional=True): t.ToInt,
    t.Key("kernel-gid", optional=True): t.ToInt,
}).allow_extra("*")
