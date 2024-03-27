import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.types import SlotTypes

from .defs import AllocationModes

RandomRange = t.Tuple(t.ToFloat, t.ToFloat)
core_idx = {0, 1, 2, 3, 4}


dummy_device_config = t.Dict({
    t.Key("device-id"): t.String(),
    t.Key("device-name"): t.String(),
    t.Key("slot-type", default=SlotTypes.COUNT): tx.Enum(SlotTypes),
    t.Key("allocation-mode", default=AllocationModes.DISCRETE): tx.Enum(AllocationModes),
    t.Key("hw-location", default="hw-location"): t.String(),
    t.Key("memory-size", default=10): t.ToInt(),
    t.Key("processing-units", default=1): t.ToInt(),
    t.Key("numa-node", default=None): t.Null | t.ToInt(),
    t.Key("model-name", default=None): t.Null | t.String(),
    t.Key("mother-uuid", default=None): t.Null | t.String(),
})

dummy_local_config = t.Dict({
    t.Key("agent"): t.Dict({
        t.Key("intrinsic"): t.Dict({
            t.Key("cpu"): t.Dict({
                t.Key("core-indexes", default=core_idx): tx.ToSet,
            }),
            t.Key("memory"): t.Dict({
                t.Key("size", default=34359738368): t.Int,
            }),
        }),
        t.Key("delay"): t.Dict({
            t.Key("scan-image", default=0.1): tx.Delay,
            t.Key("pull-image", default=1.0): tx.Delay,
            t.Key("destroy-kernel", default=1.0): tx.Delay,
            t.Key("clean-kernel", default=1.0): tx.Delay,
            t.Key("create-network", default=1.0): tx.Delay,
            t.Key("destroy-network", default=1.0): tx.Delay,
        }),
        t.Key("image"): t.Dict({
            t.Key("already-have", default=None): t.Null
            | t.Mapping(
                t.String, t.String(allow_blank=True)
            ),  # Key: a string of image canonical, Value: hash. it can be a random string.
            t.Key("need-to-pull", default=None): t.Null
            | t.List(t.String),  # A string list of image canonical
            t.Key("missing", default=None): t.Null
            | t.List(t.String),  # A string list of image canonical
        }),
    }),
    t.Key("kernel-creation-ctx"): t.Dict({
        t.Key("delay"): t.Dict({
            t.Key("prepare-scratch", default=1.0): tx.Delay,
            t.Key("prepare-ssh", default=1.0): tx.Delay,
            t.Key("spawn", default=0.5): tx.Delay,
            t.Key("start-container", default=2.0): tx.Delay,
            t.Key("mount-krunner", default=1.0): tx.Delay,
        })
    }),
    t.Key("kernel"): t.Dict({
        t.Key("use-fake-code-runner", default=True): t.Bool,
        t.Key("delay"): t.Dict({
            t.Key("check-status", default=0.1): tx.Delay,
            t.Key("get-completions", default=0.1): tx.Delay,
            t.Key("get-logs", default=0.1): tx.Delay,
            t.Key("interrupt-kernel", default=0.1): tx.Delay,
            t.Key("start-service", default=0.1): tx.Delay,
            t.Key("start-model-service", default=0.1): tx.Delay,
            t.Key("shutdown-service", default=0.1): tx.Delay,
            t.Key("commit", default=5.0): tx.Delay,
            t.Key("get-service-apps", default=0.1): tx.Delay,
            t.Key("accept-file", default=0.1): tx.Delay,
            t.Key("download-file", default=0.1): tx.Delay,
            t.Key("download-single", default=0.1): tx.Delay,
            t.Key("list-files", default=0.1): tx.Delay,
        }),
    }),
})
