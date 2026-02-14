from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.session.types import (
    CreationConfigV1,
    CreationConfigV2,
    CreationConfigV3,
    CreationConfigV3Template,
    CreationConfigV4,
    CreationConfigV4Template,
    CreationConfigV5,
    CreationConfigV5Template,
    CreationConfigV6,
    CreationConfigV6Template,
    CreationConfigV7,
    MountOption,
    ResourceOpts,
)
from ai.backend.common.types import BinarySize, MountPermission, MountTypes


class TestResourceOpts:
    def test_defaults(self) -> None:
        opts = ResourceOpts()
        assert opts.shmem is None
        assert opts.allow_fractional_resource_fragmentation is None

    def test_with_shmem(self) -> None:
        opts = ResourceOpts.model_validate({"shmem": BinarySize.from_str("1g")})
        assert opts.shmem is not None

    def test_extra_fields_allowed(self) -> None:
        opts = ResourceOpts.model_validate({"custom_key": "custom_val"})
        assert opts.model_extra is not None
        assert opts.model_extra["custom_key"] == "custom_val"


class TestMountOption:
    def test_defaults(self) -> None:
        opt = MountOption()
        assert opt.type == MountTypes.BIND
        assert opt.permission is None

    def test_with_permission_alias(self) -> None:
        opt = MountOption.model_validate({"perm": "ro"})
        assert opt.permission == MountPermission.READ_ONLY

    def test_extra_fields_allowed(self) -> None:
        opt = MountOption.model_validate({"type": "bind", "extra": True})
        assert opt.model_extra is not None
        assert opt.model_extra["extra"] is True


class TestCreationConfigV1:
    def test_defaults(self) -> None:
        cfg = CreationConfigV1()
        assert cfg.mounts is None
        assert cfg.environ is None
        assert cfg.cluster_size is None

    def test_with_values(self) -> None:
        cfg = CreationConfigV1.model_validate({
            "mounts": ["/data"],
            "environ": {"KEY": "VAL"},
            "clusterSize": 2,
        })
        assert cfg.mounts == ["/data"]
        assert cfg.environ == {"KEY": "VAL"}
        assert cfg.cluster_size == 2

    def test_cluster_size_min(self) -> None:
        with pytest.raises(ValidationError):
            CreationConfigV1.model_validate({"cluster_size": 0})


class TestCreationConfigV2:
    def test_instance_resources(self) -> None:
        cfg = CreationConfigV2.model_validate({
            "instanceMemory": BinarySize.from_str("512m"),
            "instanceCores": 4,
            "instanceGPUs": 1.5,
            "instanceTPUs": 2,
        })
        assert cfg.instance_memory is not None
        assert cfg.instance_cores == 4
        assert cfg.instance_gpus == 1.5
        assert cfg.instance_tpus == 2


class TestCreationConfigV3:
    def test_with_resource_opts(self) -> None:
        cfg = CreationConfigV3.model_validate({
            "resources": {"cpu": 2},
            "resourceOpts": {"shmem": BinarySize.from_str("256m")},
            "scalingGroup": "default",
        })
        assert cfg.resources == {"cpu": 2}
        assert cfg.resource_opts is not None
        assert cfg.scaling_group == "default"


class TestCreationConfigV3Template:
    def test_all_none_defaults(self) -> None:
        cfg = CreationConfigV3Template()
        assert cfg.mounts is None
        assert cfg.environ is None
        assert cfg.cluster_size is None
        assert cfg.scaling_group is None
        assert cfg.resources is None
        assert cfg.resource_opts is None


class TestCreationConfigV4:
    def test_mount_map_and_preopen_ports(self) -> None:
        cfg = CreationConfigV4.model_validate({
            "mountMap": {"src": "/dst"},
            "preopenPorts": [8080, 9090],
        })
        assert cfg.mount_map == {"src": "/dst"}
        assert cfg.preopen_ports == [8080, 9090]


class TestCreationConfigV4Template:
    def test_all_none_defaults(self) -> None:
        cfg = CreationConfigV4Template()
        assert cfg.mounts is None
        assert cfg.mount_map is None
        assert cfg.resource_opts is None


class TestCreationConfigV5:
    def test_mount_options(self) -> None:
        cfg = CreationConfigV5.model_validate({
            "mountOptions": {
                "my-vfolder": {"type": "bind", "perm": "rw"},
            },
            "agentList": ["agent-001"],
        })
        assert cfg.mount_options is not None
        assert cfg.mount_options["my-vfolder"].type == MountTypes.BIND
        assert cfg.mount_options["my-vfolder"].permission == MountPermission.READ_WRITE
        assert cfg.agent_list == ["agent-001"]


class TestCreationConfigV5Template:
    def test_all_none_defaults(self) -> None:
        cfg = CreationConfigV5Template()
        assert cfg.mounts is None
        assert cfg.scaling_group is None


class TestCreationConfigV6:
    def test_attach_network(self) -> None:
        net_id = uuid4()
        cfg = CreationConfigV6.model_validate({
            "attachNetwork": str(net_id),
        })
        assert cfg.attach_network == net_id


class TestCreationConfigV6Template:
    def test_attach_network_none(self) -> None:
        cfg = CreationConfigV6Template()
        assert cfg.attach_network is None


class TestCreationConfigV7:
    def test_mount_ids_and_id_map(self) -> None:
        mount_id = uuid4()
        cfg = CreationConfigV7.model_validate({
            "mount_ids": [str(mount_id)],
            "mountIdMap": {str(mount_id): "/data"},
        })
        assert cfg.mount_ids == [mount_id]
        assert cfg.mount_id_map is not None
        assert cfg.mount_id_map[mount_id] == "/data"

    def test_deprecated_mounts_still_accepted(self) -> None:
        cfg = CreationConfigV7.model_validate({
            "mounts": ["/old-data"],
            "mount_map": {"old": "/path"},
        })
        assert cfg.mounts == ["/old-data"]
        assert cfg.mount_map == {"old": "/path"}
