"""Per-role vfolder mount resolution rule.

Copies the controller-resolved :class:`VFolderMount` tuple from the
preparation context onto each kernel group in the draft, narrowed to the
``MountInfoEntry`` fields session creation consumes. Resolution itself
(accessibility check, dot-prefix auto-mount, host path materialization,
frozen permissions) is performed by the controller inside its readonly
batch-fetch transaction — a pure preparer rule would need to issue DB
reads otherwise, breaking the ``prepare`` signature's "no IO"
invariant. See
:attr:`SessionSpecContext.vfolder_mounts_by_role`.

Runs before :class:`.expand_kernel_groups_rule.ExpandKernelGroupsRule`
so the stored group carries the mounts its replicas start with; each
group reads its own ``role`` to fetch its tuple. Task #33 (role-based
mount override) slots in naturally — the controller fetch emits
distinct tuples per role and this rule keeps working unchanged.
"""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import MountInfoEntry, VFolderMount
from ai.backend.manager.data.session.draft import SessionResourceSpecDraft
from ai.backend.manager.sokovan.scheduling_controller.preparers.specs.draft_rule import (
    SessionSpecDraftRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


def _to_mount_info_entry(mount: VFolderMount) -> MountInfoEntry:
    """Narrow a resolved mount down to the fields the group stores."""
    return MountInfoEntry(
        vfolder_id=VFolderUUID(mount.vfid.folder_id),
        mount_destination=str(mount.kernel_path),
        mount_perm=mount.mount_perm,
        subpath=str(mount.vfsubpath),
    )


class ResolveVFolderMountsRule(SessionSpecDraftRule):
    """Replace each group's mount requests with the context's resolved entries."""

    @override
    def name(self) -> str:
        return "resolve_vfolder_mounts"

    @override
    async def prepare(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        resolved = context.user.vfolder_mounts_by_role
        groups = draft.resource.options.kernel_groups
        # An empty map means a resource-only caller (compute-schedule) that
        # never resolved mounts — leave the request entries untouched.
        if not resolved or not groups:
            return draft
        updated = []
        for group in groups:
            entries = tuple(_to_mount_info_entry(mount) for mount in resolved.get(group.role, ()))
            if entries == group.execution_spec.mounts:
                updated.append(group)
                continue
            updated.append(
                group.model_copy(
                    update={
                        "execution_spec": group.execution_spec.model_copy(
                            update={"mounts": entries}
                        )
                    }
                )
            )
        new_options = draft.resource.options.model_copy(update={"kernel_groups": tuple(updated)})
        return draft.model_copy(
            update={"resource": draft.resource.model_copy(update={"options": new_options})}
        )
