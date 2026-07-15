"""Tests for ``SessionSpec``-based validator rules."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Any

import pytest

from ai.backend.common.identifier.domain import DomainID, DomainName
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.types import (
    AccessKey,
    BinarySize,
    ClusterMode,
    DefaultForUnspecified,
    MountPermission,
    ResourceSlot,
    ResourceSlotEntry,
    SessionTypes,
    SlotName,
    SlotTypes,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.manager.data.dotfile.types import DotfileBundle, DotfileEntry
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData, SlotTypePolicy
from ai.backend.manager.data.session.creation import ImageInfo
from ai.backend.manager.data.session.options import (
    KernelExecutionSpec,
    KernelResourceConfig,
    ResourceOpts,
    SchedulingTarget,
    SessionHandlerOptions,
    SessionOptions,
)
from ai.backend.manager.data.session.spec import (
    KernelSpec,
    SessionClassification,
    SessionIdentity,
    SessionNetwork,
    SessionResourceSpec,
    SessionScope,
    SessionSpec,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.errors.storage import DotfileVFolderPathConflict
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.sokovan.scheduling_controller.validators.container_limit_rule import (
    ContainerLimitRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.dotfile_vfolder_conflict_rule import (
    DotfileVFolderConflictRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.image_slot_type_rule import (
    ImageSlotTypeRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.inference_model_folder_rule import (
    InferenceModelFolderRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.mount_name_validation_rule import (
    MountNameValidationRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.requested_slot_type_rule import (
    RequestedSlotTypeRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.required_resource_slot_rule import (
    RequiredResourceSlotRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.resource_limit_rule import (
    ResourceLimitRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.service_port_rule import (
    ServicePortRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidationContext,
)


def _vfolder_mount(
    name: str = "data",
    *,
    kernel_path: str | None = None,
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL,
) -> VFolderMount:
    return VFolderMount(
        name=name,
        vfid=VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()),
        vfsubpath=PurePosixPath("."),
        host_path=PurePosixPath(f"/mnt/host/{name}"),
        kernel_path=PurePosixPath(kernel_path or f"/home/work/{name}"),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=usage_mode,
    )


def _kernel(
    image_id: ImageID,
    *,
    cpu: str = "1",
    preopen_ports: tuple[int, ...] = (),
    shmem: BinarySize | None = None,
) -> KernelSpec:
    return KernelSpec(
        cluster_role="main",
        cluster_idx=1,
        cluster_hostname="main1",
        local_rank=0,
        preopen_ports=preopen_ports,
        execution_spec=KernelExecutionSpec(
            resource_input=KernelResourceConfig(
                image_id=image_id,
                resources=[
                    ResourceSlotEntry(resource_type="cpu", quantity=str(Decimal(cpu))),
                    ResourceSlotEntry(
                        resource_type="mem", quantity=str(Decimal(1024 * 1024 * 1024))
                    ),
                ],
                resource_opts=ResourceOpts(shmem=shmem),
            ),
        ),
    )


def _spec(
    kernel_specs: tuple[KernelSpec, ...],
    *,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
    vfolder_mounts: tuple[VFolderMount, ...] = (),
) -> SessionSpec:
    # SessionSpec no longer carries session-level vfolder_mounts — they live
    # per-kernel on KernelSpec.vfolder_mounts. Mirror the supplied mounts onto
    # every kernel so existing tests keep the same semantics.
    decorated_kernel_specs = tuple(
        kernel.model_copy(update={"vfolder_mounts": vfolder_mounts}) for kernel in kernel_specs
    )
    return SessionSpec(
        resource_spec=SessionResourceSpec(
            identity=SessionIdentity(
                session_id=SessionID(uuid.uuid4()),
                creation_id="c-1",
                session_name="s",
                access_key=AccessKey("AK"),
                user_uuid=uuid.uuid4(),
            ),
            classification=SessionClassification(session_type=session_type),
            network=SessionNetwork(network_type=NetworkType.VOLATILE),
            options=SessionOptions(
                priority=10,
                is_preemptible=True,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=len(kernel_specs),
                scheduling_target=SchedulingTarget(),
                kernel_groups=[],
                handler_options=SessionHandlerOptions(),
            ),
            kernel_specs=decorated_kernel_specs,
        ),
        scope=SessionScope(
            domain_id=DomainID(uuid.uuid4()),
            domain_name=DomainName("default"),
            project_id=ProjectID(uuid.uuid4()),
            resource_group_id=ResourceGroupID(uuid.uuid4()),
            resource_group_name=ResourceGroupName("default"),
        ),
    )


def _ctx(
    *,
    keypair_policy: KeyPairResourcePolicyData | None = None,
    image_infos: dict[ImageID, ImageInfo] | None = None,
    known_slot_types: dict[SlotName, SlotTypes] | None = None,
    enabled_slot_names: frozenset[SlotName] | None = None,
    required_slot_names: frozenset[SlotName] | None = None,
    dotfile_data: DotfileBundle | None = None,
) -> SessionSpecValidationContext:
    known_slot_types_val = known_slot_types or {}
    enabled_val = (
        enabled_slot_names
        if enabled_slot_names is not None
        else frozenset(known_slot_types_val.keys())
    )
    return SessionSpecValidationContext(
        keypair_resource_policy=keypair_policy,
        image_infos=image_infos or {},
        known_slot_types=known_slot_types_val,
        slot_type_policy=SlotTypePolicy(
            enabled=enabled_val,
            required=required_slot_names or frozenset(),
        ),
        dotfile_data=dotfile_data or DotfileBundle(),
    )


def _image_info(
    image_id: ImageID,
    *,
    cpu_min: Any = "1",
    mem_min: Any = "256m",
    labels: dict[str, Any] | None = None,
) -> ImageInfo:
    return ImageInfo(
        id=uuid.UUID(str(image_id)),
        canonical="repo/img:tag",
        architecture="x86_64",
        registry="repo",
        labels=labels or {},
        resource_spec={
            "cpu": {"min": cpu_min, "max": None},
            "mem": {"min": mem_min, "max": None},
        },
    )


def _keypair_policy(
    *,
    max_containers: int = 4,
) -> KeyPairResourcePolicyData:
    return KeyPairResourcePolicyData(
        name="test",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        default_for_unspecified=DefaultForUnspecified.LIMITED,
        total_resource_slots=ResourceSlot(),
        max_session_lifetime=0,
        max_concurrent_sessions=10,
        max_pending_session_count=None,
        max_pending_session_resource_slots=None,
        max_concurrent_sftp_sessions=0,
        max_containers_per_session=max_containers,
        idle_timeout=0,
        allowed_vfolder_hosts={},
    )


class TestContainerLimitRule:
    def test_within_limit(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img), _kernel(img)))
        ContainerLimitRule().validate(spec, _ctx(keypair_policy=_keypair_policy(max_containers=4)))

    def test_exceeds_limit(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img), _kernel(img), _kernel(img)))
        with pytest.raises(QuotaExceeded):
            ContainerLimitRule().validate(
                spec, _ctx(keypair_policy=_keypair_policy(max_containers=2))
            )

    def test_noop_without_policy(self) -> None:
        img = ImageID(uuid.uuid4())
        ContainerLimitRule().validate(_spec((_kernel(img),)), _ctx())


class TestResourceLimitRule:
    def test_requested_meets_image_min(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img, cpu="4"),))
        ctx = _ctx(image_infos={img: _image_info(img, cpu_min="2")})
        ResourceLimitRule().validate(spec, ctx)

    def test_requested_below_image_min(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img, cpu="1"),))
        ctx = _ctx(
            image_infos={img: _image_info(img, cpu_min="8")},
            known_slot_types=dict(_RG_BASE),
        )
        with pytest.raises(InvalidAPIParameters):
            ResourceLimitRule().validate(spec, ctx)

    def test_shmem_below_memory(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img, shmem=BinarySize.finite_from_str("64m")),))
        ctx = _ctx(image_infos={img: _image_info(img)})
        ResourceLimitRule().validate(spec, ctx)

    def test_shmem_exceeds_memory(self) -> None:
        img = ImageID(uuid.uuid4())
        # requested memory is 1GiB (see _kernel fixture).
        spec = _spec((_kernel(img, shmem=BinarySize.finite_from_str("2g")),))
        ctx = _ctx(image_infos={img: _image_info(img)})
        with pytest.raises(InvalidAPIParameters):
            ResourceLimitRule().validate(spec, ctx)

    def test_skips_image_min_for_slot_not_in_enabled(self) -> None:
        img = ImageID(uuid.uuid4())
        image_info = ImageInfo(
            id=uuid.UUID(str(img)),
            canonical="repo/img:tag",
            architecture="x86_64",
            registry="repo",
            labels={},
            resource_spec={
                "cpu": {"min": "1", "max": None},
                "mem": {"min": "256m", "max": None},
                "cuda.device": {"min": "1", "max": None},
            },
        )
        spec = _spec((_kernel(img, cpu="2"),))
        # cuda.device is absent from `enabled` (disabled by admin or unregistered),
        # so its image-declared min must not be enforced.
        ctx = _ctx(
            image_infos={img: image_info},
            known_slot_types=dict(_RG_BASE),
        )
        ResourceLimitRule().validate(spec, ctx)


class TestServicePortRule:
    def test_ok_when_no_preopen(self) -> None:
        img = ImageID(uuid.uuid4())
        ServicePortRule().validate(_spec((_kernel(img),)), _ctx())

    def test_rejects_reserved_port(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img, preopen_ports=(2200,)),))
        with pytest.raises(InvalidAPIParameters):
            ServicePortRule().validate(spec, _ctx())

    def test_rejects_image_service_port(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img, preopen_ports=(8080,)),))
        ctx = _ctx(
            image_infos={
                img: _image_info(img, labels={"ai.backend.service-ports": "jupyter:http:8080"})
            }
        )
        with pytest.raises(InvalidAPIParameters):
            ServicePortRule().validate(spec, ctx)

    def test_accepts_safe_preopen(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img, preopen_ports=(9000, 9001)),))
        ctx = _ctx(
            image_infos={
                img: _image_info(img, labels={"ai.backend.service-ports": "jupyter:http:8080"})
            }
        )
        ServicePortRule().validate(spec, ctx)


class TestMountNameValidationRule:
    def test_unique_paths_pass(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec(
            (_kernel(img),),
            vfolder_mounts=(_vfolder_mount("a"), _vfolder_mount("b")),
        )
        MountNameValidationRule().validate(spec, _ctx())

    def test_rejects_duplicate_mount_paths(self) -> None:
        img = ImageID(uuid.uuid4())
        first = _vfolder_mount("data")
        dup = VFolderMount(
            name="data-alt",
            vfid=VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()),
            vfsubpath=PurePosixPath("."),
            host_path=PurePosixPath("/mnt/host/data-alt"),
            kernel_path=PurePosixPath("/home/work/data"),
            mount_perm=MountPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
        )
        spec = _spec((_kernel(img),), vfolder_mounts=(first, dup))
        with pytest.raises(InvalidAPIParameters):
            MountNameValidationRule().validate(spec, _ctx())

    def test_rejects_reserved_alias(self) -> None:
        img = ImageID(uuid.uuid4())
        reserved = VFolderMount(
            name=".ssh",
            vfid=VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()),
            vfsubpath=PurePosixPath("."),
            host_path=PurePosixPath("/mnt/host/ssh"),
            kernel_path=PurePosixPath("/home/work/.ssh"),
            mount_perm=MountPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
        )
        spec = _spec((_kernel(img),), vfolder_mounts=(reserved,))
        with pytest.raises(InvalidAPIParameters):
            MountNameValidationRule().validate(spec, _ctx())


class TestInferenceModelFolderRule:
    def test_noop_for_non_inference(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),), session_type=SessionTypes.INTERACTIVE)
        InferenceModelFolderRule().validate(spec, _ctx())

    def test_rejects_inference_without_model_folder(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),), session_type=SessionTypes.INFERENCE)
        with pytest.raises(InvalidAPIParameters):
            InferenceModelFolderRule().validate(spec, _ctx())

    def test_accepts_inference_with_model_folder(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec(
            (_kernel(img),),
            session_type=SessionTypes.INFERENCE,
            vfolder_mounts=(_vfolder_mount("m", usage_mode=VFolderUsageMode.MODEL),),
        )
        InferenceModelFolderRule().validate(spec, _ctx())


class TestDotfileVFolderConflictRule:
    def test_noop_without_dotfiles(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),), vfolder_mounts=(_vfolder_mount("data"),))
        DotfileVFolderConflictRule().validate(spec, _ctx())

    def test_noop_without_mounts(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),))
        ctx = _ctx(
            dotfile_data=DotfileBundle(
                dotfiles=(DotfileEntry(path="/home/work/.bashrc", perm="0644", data=""),),
            )
        )
        DotfileVFolderConflictRule().validate(spec, ctx)

    def test_detects_conflict(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec(
            (_kernel(img),),
            vfolder_mounts=(_vfolder_mount("data", kernel_path="/home/work/.bashrc"),),
        )
        ctx = _ctx(
            dotfile_data=DotfileBundle(
                dotfiles=(DotfileEntry(path=".bashrc", perm="0644", data=""),),
            )
        )
        with pytest.raises(DotfileVFolderPathConflict):
            DotfileVFolderConflictRule().validate(spec, ctx)

    def test_passes_when_no_overlap(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec(
            (_kernel(img),),
            vfolder_mounts=(_vfolder_mount("data", kernel_path="/home/work/data"),),
        )
        ctx = _ctx(
            dotfile_data=DotfileBundle(
                dotfiles=(DotfileEntry(path="/etc/profile", perm="0644", data=""),),
            )
        )
        DotfileVFolderConflictRule().validate(spec, ctx)


def _image_info_with_slots(
    image_id: ImageID,
    *,
    slot_keys: tuple[str, ...],
) -> ImageInfo:
    return ImageInfo(
        id=uuid.UUID(str(image_id)),
        canonical="repo/img:tag",
        architecture="x86_64",
        registry="repo",
        labels={},
        resource_spec={k: {"min": "1", "max": None} for k in slot_keys},
    )


def _kernel_with_resources(
    image_id: ImageID,
    *,
    resources: tuple[tuple[str, str], ...],
) -> KernelSpec:
    return KernelSpec(
        cluster_role="main",
        cluster_idx=1,
        cluster_hostname="main1",
        local_rank=0,
        execution_spec=KernelExecutionSpec(
            resource_input=KernelResourceConfig(
                image_id=image_id,
                resources=[ResourceSlotEntry(resource_type=k, quantity=q) for k, q in resources],
                resource_opts=ResourceOpts(),
            ),
        ),
    )


_RG_BASE: dict[SlotName, SlotTypes] = {
    SlotName("cpu"): SlotTypes.COUNT,
    SlotName("mem"): SlotTypes.BYTES,
}


class TestImageSlotTypeRule:
    def test_passes_when_image_slots_served_by_rg(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),))
        ctx = _ctx(
            image_infos={img: _image_info_with_slots(img, slot_keys=("cpu", "mem"))},
            known_slot_types=dict(_RG_BASE),
        )
        ImageSlotTypeRule().validate(spec, ctx)

    def test_rejects_image_slot_not_served_by_rg(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),))
        ctx = _ctx(
            image_infos={img: _image_info_with_slots(img, slot_keys=("cpu", "mem", "cuda.device"))},
            known_slot_types={**_RG_BASE, SlotName("cuda.shares"): SlotTypes.COUNT},
            enabled_slot_names=frozenset({
                SlotName("cpu"),
                SlotName("mem"),
                SlotName("cuda.shares"),
                SlotName("cuda.device"),
            }),
        )
        with pytest.raises(InvalidAPIParameters):
            ImageSlotTypeRule().validate(spec, ctx)

    def test_rejects_when_rg_has_no_active_agents(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),))
        ctx = _ctx(
            image_infos={img: _image_info_with_slots(img, slot_keys=("cpu", "mem"))},
        )
        with pytest.raises(InvalidAPIParameters):
            ImageSlotTypeRule().validate(spec, ctx)

    def test_noop_without_image_info(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),))
        ctx = _ctx(known_slot_types=dict(_RG_BASE))
        ImageSlotTypeRule().validate(spec, ctx)

    def test_skips_image_slot_when_min_is_zero(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),))
        image_info = ImageInfo(
            id=uuid.UUID(str(img)),
            canonical="repo/img:tag",
            architecture="x86_64",
            registry="repo",
            labels={},
            resource_spec={
                "cpu": {"min": "1", "max": None},
                "mem": {"min": "1", "max": None},
                "cuda.device": {"min": "0", "max": None},
            },
        )
        ctx = _ctx(
            image_infos={img: image_info},
            known_slot_types=dict(_RG_BASE),
        )
        ImageSlotTypeRule().validate(spec, ctx)

    def test_skips_image_slot_not_in_enabled(self) -> None:
        # cuda.device is declared by the image but absent from `enabled`,
        # so the image-side check ignores it instead of rejecting the session.
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),))
        ctx = _ctx(
            image_infos={img: _image_info_with_slots(img, slot_keys=("cpu", "mem", "cuda.device"))},
            known_slot_types=dict(_RG_BASE),
        )
        ImageSlotTypeRule().validate(spec, ctx)

    def test_rejects_image_slot_when_enabled_but_not_served(self) -> None:
        # cuda.device is globally enabled but the RG has no agent serving it,
        # so the image's declaration cannot be satisfied here.
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel(img),))
        ctx = _ctx(
            image_infos={img: _image_info_with_slots(img, slot_keys=("cpu", "mem", "cuda.device"))},
            known_slot_types=dict(_RG_BASE),
            enabled_slot_names=frozenset({
                SlotName("cpu"),
                SlotName("mem"),
                SlotName("cuda.device"),
            }),
        )
        with pytest.raises(InvalidAPIParameters):
            ImageSlotTypeRule().validate(spec, ctx)


class TestRequestedSlotTypeRule:
    def test_passes_when_requested_slots_served_by_rg(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((
            _kernel_with_resources(img, resources=(("cpu", "1"), ("mem", "1073741824"))),
        ))
        ctx = _ctx(known_slot_types=dict(_RG_BASE))
        RequestedSlotTypeRule().validate(spec, ctx)

    def test_rejects_requested_slot_not_served_by_rg(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((
            _kernel_with_resources(
                img,
                resources=(("cpu", "1"), ("mem", "1073741824"), ("cuda.device", "1")),
            ),
        ))
        ctx = _ctx(known_slot_types={**_RG_BASE, SlotName("cuda.shares"): SlotTypes.COUNT})
        with pytest.raises(InvalidAPIParameters):
            RequestedSlotTypeRule().validate(spec, ctx)

    def test_rejects_when_rg_has_no_active_agents(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((_kernel_with_resources(img, resources=(("cpu", "1"),)),))
        with pytest.raises(InvalidAPIParameters):
            RequestedSlotTypeRule().validate(spec, _ctx())

    def test_skips_requested_slot_when_quantity_is_zero(self) -> None:
        img = ImageID(uuid.uuid4())
        spec = _spec((
            _kernel_with_resources(
                img,
                resources=(("cpu", "1"), ("mem", "1073741824"), ("cuda.device", "0")),
            ),
        ))
        ctx = _ctx(known_slot_types=dict(_RG_BASE))
        RequestedSlotTypeRule().validate(spec, ctx)


class TestRequiredResourceSlotRule:
    @pytest.fixture
    def image_id(self) -> ImageID:
        return ImageID(uuid.uuid4())

    @pytest.fixture
    def required_slot_ctx(self) -> SessionSpecValidationContext:
        return _ctx(required_slot_names=frozenset({SlotName("cpu"), SlotName("mem")}))

    def test_passes_when_required_slots_present(
        self,
        image_id: ImageID,
        required_slot_ctx: SessionSpecValidationContext,
    ) -> None:
        spec = _spec((
            _kernel_with_resources(image_id, resources=(("cpu", "1"), ("mem", "1073741824"))),
        ))
        RequiredResourceSlotRule().validate(spec, required_slot_ctx)

    @pytest.mark.parametrize(
        ("resources", "expected_missing_slot"),
        [
            (((("cpu", "1"),)), "mem"),
            (((("cpu", "0"), ("mem", "1073741824"))), "cpu"),
        ],
    )
    def test_rejects_missing_or_zero_required_slot(
        self,
        image_id: ImageID,
        required_slot_ctx: SessionSpecValidationContext,
        resources: tuple[tuple[str, str], ...],
        expected_missing_slot: str,
    ) -> None:
        spec = _spec((_kernel_with_resources(image_id, resources=resources),))
        with pytest.raises(InvalidAPIParameters, match=expected_missing_slot):
            RequiredResourceSlotRule().validate(spec, required_slot_ctx)
