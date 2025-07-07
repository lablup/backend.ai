from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Final, Optional, Self, override

from ai.backend.agent.resources import ComputerContext, KernelResourceSpec
from ai.backend.common.docker import KernelFeatures, LabelName
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    BinarySize,
    DeviceModelInfo,
    DeviceName,
    KernelCreationConfig,
    SlotName,
)

from ..defs import LIBBAIHOOK_MOUNT_PATH

LD_PRELOAD: Final[str] = "LD_PRELOAD"
LOCAL_USER_ID: Final[str] = "LOCAL_USER_ID"
LOCAL_GROUP_ID: Final[str] = "LOCAL_GROUP_ID"
ADDITIONAL_GIDS: Final[str] = "ADDITIONAL_GIDS"


@dataclass
class AgentInfo:
    computers: Mapping[DeviceName, ComputerContext]
    distro: str
    architecture: str
    kernel_uid: int
    kernel_gid: int


@dataclass
class KernelInfo:
    kernel_creation_config: KernelCreationConfig
    kernel_features: frozenset[str]
    resource_spec: KernelResourceSpec
    overriding_uid: Optional[int]
    overriding_gid: Optional[int]
    supplementary_gids: set[int]


@dataclass
class EnvironSpec:
    agent_info: AgentInfo
    kernel_info: KernelInfo


class EnvironSpecGenerator(ArgsSpecGenerator[EnvironSpec]):
    pass


@dataclass
class EnvironResult:
    environ: dict[str, str]


class Environ(dict[str, str]):
    def set_value(self, key: str, value: Optional[Any]) -> Self:
        if value is None:
            return self
        self[key] = str(value)
        return self

    def append_values(self, key: str, values: Collection[str], *, separator: str) -> Self:
        if not values:
            return self
        if orig_value := self.get(key):
            # If the key already exists, append the new values
            orig_val = {v for v in orig_value.split(separator) if v}
            new_values = orig_val | set(values)
        else:
            # If the key does not exist, create a new entry
            new_values = set(values)
        self[key] = separator.join(sorted(new_values))
        return self

    def update_always(self, environ: Mapping[str, str]) -> Self:
        for key, value in environ.items():
            self[key] = value
        return self

    def update_if_not_exists(self, environ: Mapping[str, str]) -> Self:
        for key, value in environ.items():
            if key not in self:
                self[key] = value
        return self

    def to_dict(self) -> dict[str, str]:
        return dict(self)


class EnvironProvisioner(Provisioner[EnvironSpec, EnvironResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "environ"

    @override
    async def setup(self, spec: EnvironSpec) -> EnvironResult:
        environ = Environ({
            **spec.kernel_info.kernel_creation_config["environ"]
        })  # Start with the base environment
        environ = (
            environ.set_value(LD_PRELOAD, LIBBAIHOOK_MOUNT_PATH)
            .set_value(LOCAL_USER_ID, self._get_local_uid(spec))
            .set_value(LOCAL_GROUP_ID, self._get_local_gid(spec))
            .append_values(ADDITIONAL_GIDS, self._get_supplementary_gids(spec), separator=",")
            .append_values(ADDITIONAL_GIDS, self._get_computer_gids(spec), separator=",")
            .update_if_not_exists(self._get_core_count(spec))
        )

        hook_paths = await self._get_container_hooks(spec)
        device_environ = await self._get_device_environ(spec)
        environ = environ.append_values(LD_PRELOAD, hook_paths, separator=":").update_always(
            device_environ
        )
        return EnvironResult(environ=environ.to_dict())

    def _get_local_uid(self, spec: EnvironSpec) -> Optional[int]:
        if spec.kernel_info.overriding_uid is not None:
            return spec.kernel_info.overriding_uid
        if KernelFeatures.UID_MATCH in spec.kernel_info.kernel_features:
            return spec.agent_info.kernel_uid
        return None

    def _get_local_gid(self, spec: EnvironSpec) -> Optional[int]:
        if spec.kernel_info.overriding_gid is not None:
            return spec.kernel_info.overriding_gid
        if KernelFeatures.UID_MATCH in spec.kernel_info.kernel_features:
            return spec.agent_info.kernel_gid
        return None

    def _get_supplementary_gids(self, spec: EnvironSpec) -> set[str]:
        return {str(gid) for gid in spec.kernel_info.supplementary_gids}

    def _get_computer_gids(self, spec: EnvironSpec) -> set[str]:
        additional_gid_set: set[int] = set()
        for dev_type in spec.kernel_info.resource_spec.allocations:
            computer_ctx = spec.agent_info.computers[dev_type]
            additional_gids = computer_ctx.instance.get_additional_gids()
            additional_gid_set.update(additional_gids)
        return {str(gid) for gid in additional_gid_set}

    def _get_core_count(self, spec: EnvironSpec) -> dict[str, str]:
        image_labels = spec.kernel_info.kernel_creation_config["image"]["labels"]
        label_envs_corecount = image_labels.get(LabelName.ENVS_CORECOUNT, "")
        envs_corecount = label_envs_corecount.split(",") if label_envs_corecount else []
        cpu_core_count = len(
            spec.kernel_info.resource_spec.allocations[DeviceName("cpu")][SlotName("cpu")]
        )
        return {k: str(cpu_core_count) for k in envs_corecount}

    async def _get_container_hooks(self, spec: EnvironSpec) -> set[str]:
        container_hook_path_set: set[str] = set()
        for dev_type, device_alloc in spec.kernel_info.resource_spec.allocations.items():
            alloc_sum = Decimal(0)
            for per_dev_alloc in device_alloc.values():
                alloc_sum += sum(per_dev_alloc.values())
            do_hook_mount = alloc_sum > 0
            if not do_hook_mount:
                continue
            computer_ctx = spec.agent_info.computers[dev_type]
            hook_paths = await computer_ctx.instance.get_hooks(
                spec.agent_info.distro, spec.agent_info.architecture
            )
            for p in hook_paths:
                hook_path = p.absolute()
                final_path = f"/opt/kernel/{hook_path.name}"
                if final_path in container_hook_path_set:
                    continue
                container_hook_path_set.add(final_path)
        return container_hook_path_set

    async def _get_device_environ(self, spec: EnvironSpec) -> dict[str, str]:
        environ: dict[str, str] = {}
        # Get attached devices information (including model_name).
        attached_devices: dict[DeviceName, Sequence[DeviceModelInfo]] = {}
        for alloc_dev_name, device_alloc in spec.kernel_info.resource_spec.allocations.items():
            computer_ctx = spec.agent_info.computers[alloc_dev_name]
            devices = await computer_ctx.instance.get_attached_devices(device_alloc)
            attached_devices[alloc_dev_name] = devices

        # Generate GPU config env-vars
        has_gpu_config = False
        for dev_name, attached_accelerators in attached_devices.items():
            if has_gpu_config:
                # Generate GPU config for the first-seen accelerator only
                continue
            if dev_name in (DeviceName("cpu"), DeviceName("mem")):
                # Skip intrinsic slots
                continue
            mem_per_device: list[str] = []
            mem_per_device_tf: list[str] = []
            # proc_items = []  # (unused yet)
            for local_idx, dev_info in enumerate(attached_accelerators):
                mem = BinarySize(dev_info["data"].get("mem", 0))
                mem_per_device.append(f"{local_idx}:{mem:s}")
                mem_in_megibytes = f"{mem // (2**20):d}"
                mem_per_device_tf.append(f"{local_idx}:{mem_in_megibytes}")
                # The processor count is not used yet!
                # NOTE: Keep backward-compatibility with the CUDA plugin ("smp")
                # proc = dev_info["data"].get("proc", dev_info["data"].get("smp", 0))
                # proc_items.append(f"{local_idx}:{proc}")
            if attached_accelerators:
                # proc_str = ",".join(proc_items)  # (unused yet)
                environ["GPU_TYPE"] = str(dev_name)
                environ["GPU_MODEL_NAME"] = attached_accelerators[0]["model_name"]
                environ["GPU_CONFIG"] = ",".join(mem_per_device)
                environ["TF_GPU_MEMORY_ALLOC"] = ",".join(mem_per_device_tf)
            environ["GPU_COUNT"] = str(len(attached_accelerators))
            environ["N_GPUS"] = str(len(attached_accelerators))
            has_gpu_config = True
        if not has_gpu_config:
            environ["GPU_COUNT"] = "0"
            environ["N_GPUS"] = "0"
        return environ

    @override
    async def teardown(self, resource: EnvironResult) -> None:
        pass


class EnvironStage(ProvisionStage[EnvironSpec, EnvironResult]):
    pass
