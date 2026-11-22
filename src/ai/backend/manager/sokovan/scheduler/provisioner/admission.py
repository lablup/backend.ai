"""Units of admission: a session alone, or the pending members of an `all_or_none` group.

A group takes the queue position of its first member in the sequenced order. The
sequencer orders by priority first, so that is the group's highest member priority, then
the earliest member the strategy puts first (the earliest enqueue under FIFO).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.logging.structured import LogValue
from ai.backend.manager.views.sokovan.workload import GroupAdmission, SessionWorkload


@dataclass(frozen=True)
class AdmissionUnit:
    """Sessions admitted together: one session, or every pending member of a group."""

    workloads: Sequence[SessionWorkload]
    # The group admitted all at once; None for a single session
    group: GroupAdmission | None = None

    def log_context(self) -> dict[str, LogValue]:
        if self.group is None:
            return {"session_id": self.workloads[0].meta.session_id}
        return {"session_group_id": self.group.group_id}


def admission_units(
    sequenced: Sequence[SessionWorkload],
) -> tuple[list[AdmissionUnit], list[SessionWorkload]]:
    """Split the sequenced workloads into admission units and the held members.

    The members of an `all_or_none` group with fewer than `member_count` pending
    members are held, in sequenced order.
    """
    members: defaultdict[SessionGroupID, list[SessionWorkload]] = defaultdict(list)
    for workload in sequenced:
        if workload.group_admission is not None:
            members[workload.group_admission.group_id].append(workload)

    units: list[AdmissionUnit] = []
    held: list[SessionWorkload] = []
    seen: set[SessionGroupID] = set()
    for workload in sequenced:
        group = workload.group_admission
        if group is None:
            units.append(AdmissionUnit(workloads=[workload]))
            continue
        if len(members[group.group_id]) < group.member_count:
            held.append(workload)
            continue
        if group.group_id in seen:
            continue
        seen.add(group.group_id)
        units.append(AdmissionUnit(workloads=members[group.group_id], group=group))
    return units, held
