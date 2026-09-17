"""Write specs for a kernel of a session and what it asked for in each slot."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import ResourceSlotEntry
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.session.creation import ImageInfo
from ai.backend.manager.data.session.options import KernelExecutionSpec, KernelResourceConfig
from ai.backend.manager.data.session.spec import KernelSpec
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.models.kernel.creators import KernelCreator
from ai.backend.manager.models.resource_slot.creators import KernelResourceAllocationCreator
from bai_scenario.seeds.seeder import SeedFieldWithNestedRows
from bai_scenario.seeds.session.session import session_spec


@dataclass(frozen=True)
class SeedKernelOf(SeedFieldWithNestedRows[SessionEntityData, KernelInfo]):
    """The main kernel of the session, with what it asked for in each slot written under it.

    The session and the image are values earlier rows answered. The kernel waits as
    enqueued, so what it asked for is recorded but nothing is held on an agent yet.
    """

    session: SessionEntityData
    image: ImageData
    slots: tuple[tuple[str, Decimal], ...]

    @override
    def kind(self) -> str:
        asked = ", ".join(f"{name} {amount}" for name, amount in self.slots)
        return f"요구량이 {asked}인 커널 하나를 갖는다"

    @override
    def owner_id(self, owner: SessionEntityData) -> SessionID:
        return SessionID(owner.id)

    @override
    def field(self) -> KernelCreator:
        if self.session.name is None or self.session.access_key is None:
            raise LookupError("the session was laid without a name or an access key")
        kernel_spec = KernelSpec(
            cluster_role="main",
            cluster_idx=1,
            cluster_hostname="main1",
            local_rank=0,
            execution_spec=KernelExecutionSpec(
                resource_input=KernelResourceConfig(
                    image_id=ImageID(self.image.id),
                    resources=[
                        ResourceSlotEntry(
                            resource_type=ResourceSlotName(name), quantity=str(amount)
                        )
                        for name, amount in self.slots
                    ],
                )
            ),
        )
        return KernelCreator(
            spec=session_spec(
                session_id=SessionID(self.session.id),
                name=self.session.name,
                access_key=self.session.access_key,
                user_uuid=self.session.user_uuid,
                domain_id=self.session.domain_id,
                domain_name=self.session.domain_name,
                project_id=self.session.group_id,
                resource_group_id=self.session.resource_group_id,
                resource_group_name=self.session.resource_group_name,
                kernel_specs=(kernel_spec,),
            ),
            kernel_spec=kernel_spec,
            image_info=ImageInfo(
                id=self.image.id,
                canonical=str(self.image.name),
                architecture=self.image.architecture,
                registry=self.image.registry,
                labels={},
                resource_spec={},
            ),
            enqueue_time=datetime.now(UTC),
        )

    @override
    def nested(self) -> Sequence[KernelResourceAllocationCreator]:
        return [
            KernelResourceAllocationCreator(slot_name=name, requested=amount)
            for name, amount in self.slots
        ]
