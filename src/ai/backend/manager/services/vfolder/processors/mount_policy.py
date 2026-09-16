from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.services.vfolder.actions.mount_policy import (
    ListVFolderMountPoliciesAction,
    ListVFolderMountPoliciesActionResult,
    SetVFolderMountPolicyAction,
    SetVFolderMountPolicyActionResult,
    UnsetVFolderMountPolicyAction,
    UnsetVFolderMountPolicyActionResult,
)
from ai.backend.manager.services.vfolder.services.mount_policy import VFolderMountPolicyService


class VFolderMountPolicyProcessors:
    set: SingleEntityActionProcessor[SetVFolderMountPolicyAction, SetVFolderMountPolicyActionResult]
    unset: SingleEntityActionProcessor[
        UnsetVFolderMountPolicyAction, UnsetVFolderMountPolicyActionResult
    ]
    list: SingleEntityActionProcessor[
        ListVFolderMountPoliciesAction, ListVFolderMountPoliciesActionResult
    ]

    def __init__(
        self, group: ProcessorGroup[VFolderData], service: VFolderMountPolicyService
    ) -> None:
        self.set = group.single_entity(SetVFolderMountPolicyAction, service.set)
        self.unset = group.single_entity(UnsetVFolderMountPolicyAction, service.unset)
        self.list = group.single_entity(ListVFolderMountPoliciesAction, service.list)
