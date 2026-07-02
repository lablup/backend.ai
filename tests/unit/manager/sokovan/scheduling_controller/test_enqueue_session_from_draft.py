"""Module-level integration test for ``SchedulingController.enqueue_session_from_draft``.

Wires the full draft path with mocked repository, config provider, storage
manager, and hook plugin context so we can verify:

* the repository fetch is called with the caller-supplied draft + config-
  derived knobs,
* the preparer chain produces a finalized ``SessionSpec`` whose fields
  match the draft + fetched context,
* the validator chain is invoked against the built ``SessionSpec``,
* the final ``enqueue_session_from_spec`` call receives the same spec,
* the PENDING broadcast + ``POST_ENQUEUE_SESSION`` hook fire with the
  returned session id.

Intentionally a pure in-memory test — no DB, no aiohttp, no Docker —
so it runs in single-digit seconds and exercises every wire in the
controller's draft path.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.domain import DomainID, DomainName
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.plugin.hook import PASSED, HookResult, HookResults
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    MountInfoEntry,
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
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData, SlotTypePolicy
from ai.backend.manager.data.session.creation import (
    ContainerUserInfo,
    ImageInfo,
    ScalingGroupNetworkInfo,
)
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    SchedulingTargetDraft,
    SessionClassificationDraft,
    SessionIdentityDraft,
    SessionNetworkDraft,
    SessionOptionsDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import (
    DefaultSessionOptions,
    ResourceOpts,
    SessionHandlerOptions,
)
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.common import RejectedByHook
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionSpecContextFetch,
)
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)


@pytest.fixture
def image_id() -> ImageID:
    return ImageID(uuid.uuid4())


@pytest.fixture
def draft(image_id: ImageID) -> SessionSpecDraft:
    """A minimal but valid draft that satisfies every preparer rule."""
    return SessionSpecDraft(
        identity=SessionIdentityDraft(
            session_id=SessionID(uuid.uuid4()),
            creation_id="ci-1",
            session_name="module-test-session",
            access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        ),
        scope=SessionScopeDraft(
            domain_id=DomainID(uuid.uuid4()),
            domain_name=DomainName("default"),
            project_id=ProjectID(uuid.uuid4()),
            resource_group_id=ResourceGroupID(uuid.uuid4()),
            resource_group_name=ResourceGroupName("default"),
        ),
        classification=SessionClassificationDraft(session_type=SessionTypes.INTERACTIVE),
        network=SessionNetworkDraft(),
        options=SessionOptionsDraft(
            priority=10,
            is_preemptible=True,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            scheduling_target=SchedulingTargetDraft(),
            kernel_groups=(
                KernelGroupDraft(
                    role="main",
                    replica_count=1,
                    execution_spec=KernelExecutionSpecDraft(
                        image_id=image_id,
                        resources=(
                            ResourceSlotEntry(resource_type="cpu", quantity=str(Decimal(2))),
                            ResourceSlotEntry(
                                resource_type="mem",
                                quantity=str(Decimal(2 * 1024 * 1024 * 1024)),
                            ),
                        ),
                        resource_opts=ResourceOpts(),
                        mounts=(
                            MountInfoEntry(
                                vfolder_id=VFolderUUID(
                                    VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()).folder_id
                                ),
                                mount_destination="/home/work/data",
                                mount_perm=MountPermission.READ_WRITE,
                            ),
                        ),
                    ),
                ),
            ),
            handler_options=SessionHandlerOptions(),
        ),
    )


def _vfolder_mount() -> VFolderMount:
    return VFolderMount(
        name="data",
        vfid=VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()),
        vfsubpath=PurePosixPath("."),
        host_path=PurePosixPath("/mnt/host/data"),
        kernel_path=PurePosixPath("/home/work/data"),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=VFolderUsageMode.GENERAL,
    )


def _image_info(image_id: ImageID) -> ImageInfo:
    return ImageInfo(
        id=uuid.UUID(str(image_id)),
        canonical="repo/img:tag",
        architecture="x86_64",
        registry="repo",
        labels={},
        resource_spec={
            "cpu": {"min": "1", "max": None},
            "mem": {"min": "256 MiB", "max": None},
        },
    )


def _keypair_policy() -> KeyPairResourcePolicyData:
    return KeyPairResourcePolicyData(
        name="default",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        default_for_unspecified=DefaultForUnspecified.LIMITED,
        total_resource_slots=ResourceSlot(),
        max_session_lifetime=0,
        max_concurrent_sessions=10,
        max_pending_session_count=None,
        max_pending_session_resource_slots=None,
        max_concurrent_sftp_sessions=0,
        max_containers_per_session=4,
        idle_timeout=0,
        allowed_vfolder_hosts={},
    )


def _make_user() -> UserData:
    return UserData(
        user_id=uuid.UUID(int=1),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
    )


def _fetch_bundle(image_id: ImageID) -> SessionSpecContextFetch:
    return SessionSpecContextFetch(
        resource_group_defaults=DefaultSessionOptions(),
        resource_group_network=ScalingGroupNetworkInfo(use_host_network=False, wsproxy_addr=None),
        container_user_info=ContainerUserInfo(uid=1000, main_gid=1000, supplementary_gids=[]),
        image_infos={image_id: _image_info(image_id)},
        resource_group_allow_fractional=False,
        vfolder_mounts_by_role={"main": (_vfolder_mount(),)},
        dotfile_data=DotfileBundle(),
        keypair_resource_policy=_keypair_policy(),
        known_slot_types={
            SlotName("cpu"): SlotTypes.COUNT,
            SlotName("mem"): SlotTypes.BYTES,
        },
        slot_type_policy=SlotTypePolicy(
            enabled=frozenset({SlotName("cpu"), SlotName("mem")}),
        ),
    )


def _build_controller(
    repository: AsyncMock,
    *,
    hook_status: Any = PASSED,
) -> tuple[SchedulingController, MagicMock, MagicMock]:
    config_provider = MagicMock()
    etcd_loader = MagicMock()
    etcd_loader.get_vfolder_types = AsyncMock(return_value=["user"])
    etcd_loader.get_resource_slots = AsyncMock(
        return_value={SlotName("cpu"): SlotTypes.COUNT, SlotName("mem"): SlotTypes.BYTES}
    )
    config_provider.legacy_etcd_config_loader = etcd_loader

    storage_manager = MagicMock()
    event_producer = MagicMock()
    event_producer.broadcast_events_batch = AsyncMock()
    valkey_schedule = MagicMock()
    valkey_schedule.mark_schedule_needed = AsyncMock()
    network_plugin_ctx = MagicMock()

    hook_plugin_ctx = MagicMock()
    hook_result = HookResult(
        status=hook_status,
        src_plugin=None,
        result=HookResults.PASSED,
        reason=None,
    )
    hook_plugin_ctx.dispatch = AsyncMock(return_value=hook_result)
    hook_plugin_ctx.notify = AsyncMock()

    controller = SchedulingController(
        SchedulingControllerArgs(
            repository=repository,
            config_provider=config_provider,
            storage_manager=storage_manager,
            event_producer=event_producer,
            valkey_schedule=valkey_schedule,
            network_plugin_ctx=network_plugin_ctx,
            hook_plugin_ctx=hook_plugin_ctx,
        )
    )
    return controller, event_producer, hook_plugin_ctx


class TestEnqueueSessionFromDraft:
    async def test_happy_path_finalizes_spec_and_enqueues(
        self,
        draft: SessionSpecDraft,
        image_id: ImageID,
    ) -> None:
        expected_session_id = SessionID(uuid.uuid4())

        repository = AsyncMock()
        repository.fetch_session_spec_contexts.return_value = _fetch_bundle(image_id)
        repository.enqueue_session_from_spec.return_value = expected_session_id
        repository.mark_scheduling_needed = AsyncMock()

        controller, event_producer, hook_plugin_ctx = _build_controller(repository)

        user = _make_user()

        with with_user(user):
            returned_id = await controller.enqueue_session_from_draft(draft)

        assert returned_id == expected_session_id

        # Repository fetch got the draft + config-sourced knobs
        repository.fetch_session_spec_contexts.assert_awaited_once()
        call_kwargs = repository.fetch_session_spec_contexts.await_args.kwargs
        assert call_kwargs["allowed_vfolder_types"] == ["user"]
        assert repository.fetch_session_spec_contexts.await_args.args[0] is draft

        # enqueue_session_from_spec got the finalized SessionSpec
        repository.enqueue_session_from_spec.assert_awaited_once()
        enqueued_spec = repository.enqueue_session_from_spec.await_args.args[0]
        assert isinstance(enqueued_spec, SessionSpec)
        assert enqueued_spec.identity.session_id == draft.identity.session_id
        assert enqueued_spec.identity.session_name == draft.identity.session_name
        assert enqueued_spec.options.cluster_size == 1
        assert len(enqueued_spec.kernel_specs) == 1
        kernel = enqueued_spec.kernel_specs[0]
        assert kernel.cluster_role == "main"
        assert kernel.execution_spec.image_id == image_id
        # vfolder mounts flowed through context → resolved on the kernel spec
        assert len(kernel.vfolder_mounts) == 1
        assert kernel.vfolder_mounts[0].kernel_path == PurePosixPath("/home/work/data")

        # PRE + POST hooks fired
        assert hook_plugin_ctx.dispatch.await_count == 1
        assert hook_plugin_ctx.notify.await_count == 1

        # PENDING broadcast fired once
        event_producer.broadcast_events_batch.assert_awaited_once()
        broadcast_batch = event_producer.broadcast_events_batch.await_args.args[0]
        assert len(broadcast_batch) == 1
        assert broadcast_batch[0].session_id == expected_session_id

    async def test_pre_enqueue_hook_rejection_raises(
        self,
        draft: SessionSpecDraft,
        image_id: ImageID,
    ) -> None:
        repository = AsyncMock()
        repository.fetch_session_spec_contexts.return_value = _fetch_bundle(image_id)
        repository.enqueue_session_from_spec = AsyncMock()

        controller, _event_producer, _hook_plugin_ctx = _build_controller(
            repository, hook_status="REJECTED"
        )

        user = _make_user()

        with with_user(user), pytest.raises(RejectedByHook):
            await controller.enqueue_session_from_draft(draft)

        # Writer path must not be reached
        repository.enqueue_session_from_spec.assert_not_called()

    async def test_assigns_network_type_volatile_when_not_host(
        self,
        draft: SessionSpecDraft,
        image_id: ImageID,
    ) -> None:
        repository = AsyncMock()
        repository.fetch_session_spec_contexts.return_value = _fetch_bundle(image_id)
        repository.enqueue_session_from_spec.return_value = SessionID(uuid.uuid4())
        repository.mark_scheduling_needed = AsyncMock()

        controller, _event_producer, _hook_plugin_ctx = _build_controller(repository)

        user = _make_user()
        with with_user(user):
            await controller.enqueue_session_from_draft(draft)

        enqueued_spec = repository.enqueue_session_from_spec.await_args.args[0]
        assert enqueued_spec.network.network_type == NetworkType.VOLATILE
