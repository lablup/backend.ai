"""What the recovery record does with a kernel that is not Docker's.

The failure this pins is the one a new container runtime walks into. The registry used to answer
`None` for any kernel it did not recognise, and the writer skipped it: the backend started, ran
sessions, wrote no record for any of them, logged "Saved kernel registry" all the same, and lost
every kernel at the next restart. Nothing distinguishes "wrote no entries" from "had no entries",
so the first time anybody finds out is an upgrade with live sessions.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.exception import UnsupportedKernelType
from ai.backend.agent.kernel_registry.types import DOCKER_KERNEL_TYPE, KernelRecoveryData
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.scratch.types import KernelRecoveryScratchData
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, ResourceSlot, SessionId, SessionTypes


def _resource_spec() -> KernelResourceSpec:
    return KernelResourceSpec(slots=ResourceSlot(), allocations={}, scratch_disk_size=0)


def _record(**overrides: object) -> KernelRecoveryData:
    kernel_id = KernelId(uuid.uuid4())
    base: dict[str, object] = {
        "id": kernel_id,
        "agent_id": AgentId("i-dk-104"),
        "image_ref": ImageRef(
            name="python",
            project="stable",
            tag="3.13-ubuntu24.04",
            registry="cr.backend.ai",
            architecture="x86_64",
            is_local=False,
        ),
        "version": 1,
        "ownership_data": KernelOwnershipData(
            kernel_id=kernel_id,
            session_id=SessionId(uuid.uuid4()),
            agent_id=AgentId("i-dk-104"),
        ),
        "network_id": "n1",
        "network_driver": "bridge",
        "session_type": SessionTypes.INTERACTIVE,
        "block_service_ports": False,
        "domain_socket_proxies": [],
        "service_ports": [],
        "repl_in_port": 2000,
        "repl_out_port": 2001,
        "resource_spec": _resource_spec(),
        "environ": {},
    }
    return KernelRecoveryData(**{**base, **overrides})  # type: ignore[arg-type]


class TestAKernelThisBuildCannotRecordIsRefused:
    def test_an_unknown_kernel_class_raises(self) -> None:
        """Not `None`. A backend added without its case here finds out at once."""

        class PodmanKernel(AbstractKernel):  # a stand-in for any runtime added later
            pass

        with pytest.raises(UnsupportedKernelType):
            KernelRecoveryData.from_kernel(MagicMock(spec=PodmanKernel))

    def test_the_message_says_what_to_add(self) -> None:
        """A refusal nobody can act on is a refusal that gets worked around."""

        class ApptainerKernel(AbstractKernel):
            pass

        with pytest.raises(UnsupportedKernelType) as caught:
            KernelRecoveryData.from_kernel(MagicMock(spec=ApptainerKernel))
        assert "from_kernel" in str(caught.value)


class TestARecordRebuildsAsItsOwnKernel:
    def test_an_unknown_kernel_type_raises(self) -> None:
        """The other direction: a record written by a build that knows a backend this one does
        not. Rebuilding it as a `DockerKernel` would hand this agent a kernel object whose runtime
        methods drive the wrong runtime."""
        with pytest.raises(UnsupportedKernelType):
            _record(kernel_type="podman").to_kernel()

    def test_a_record_from_before_the_field_reads_as_docker(self) -> None:
        """Docker is the only backend that ever wrote one, so absence is not ambiguous."""
        assert KernelRecoveryData.model_fields["kernel_type"].default == DOCKER_KERNEL_TYPE
        assert KernelRecoveryScratchData.model_fields["kernel_type"].default == DOCKER_KERNEL_TYPE

    def test_the_type_survives_the_scratch_round_trip(self) -> None:
        """The scratch record is what a restart actually reads; losing the type there loses it."""
        record = _record(kernel_type="podman")
        scratch = KernelRecoveryScratchData.from_kernel_recovery_data(record)
        assert scratch.kernel_type == "podman"

        back = scratch.to_kernel_recovery_data(_resource_spec(), {})
        assert back.kernel_type == "podman"

    def test_a_docker_record_still_round_trips(self) -> None:
        record = _record()
        assert record.kernel_type == DOCKER_KERNEL_TYPE
        scratch = KernelRecoveryScratchData.from_kernel_recovery_data(record)
        assert scratch.to_kernel_recovery_data(_resource_spec(), {}).kernel_type == (
            DOCKER_KERNEL_TYPE
        )
