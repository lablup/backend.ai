from __future__ import annotations

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairFieldType
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.ops.result import ScopedFieldsOpsResult
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.services.ssh_keypair.actions.lookup_owner import (
    LookupBulkSSHKeypairOwnerAction,
    LookupSSHKeypairOwnerAction,
)
from ai.backend.manager.services.ssh_keypair.actions.search import SearchSSHKeypairsAction
from ai.backend.manager.services.ssh_keypair.actions.switch_default import (
    SwitchDefaultSSHKeypairAction,
    SwitchDefaultSSHKeypairActionResult,
)
from ai.backend.manager.services.ssh_keypair.actions.upload import (
    UploadSSHKeypairAction,
    UploadSSHKeypairActionResult,
)
from ai.backend.manager.services.ssh_keypair.service import SSHKeypairService


class SSHKeypairProcessors:
    """An SSH keypair is a field row of its user. ``upload`` names the user and runs through
    ``group``; the operations naming a keypair by its id run through ``fields``, where the
    owning user answers."""

    fields: LookupFieldGroup[SSHKeypairData]
    search: BulkActionProcessor[SearchSSHKeypairsAction, ScopedFieldsOpsResult[SSHKeypairData]]
    upload: SingleEntityActionProcessor[UploadSSHKeypairAction, UploadSSHKeypairActionResult]
    switch_default: SingleFieldActionProcessor[
        SwitchDefaultSSHKeypairAction, SwitchDefaultSSHKeypairActionResult
    ]

    def __init__(self, group: ProcessorGroup[UserData], service: SSHKeypairService) -> None:
        self.fields = group.field_group(
            FieldGroupMeta(SSHKeypairFieldType()),
            SSHKeypairData,
            LookupSSHKeypairOwnerAction,
            LookupBulkSSHKeypairOwnerAction,
        )
        self.search = self.fields.atomic_bulk_scoped_search_ops(SearchSSHKeypairsAction)
        self.upload = group.single_entity(UploadSSHKeypairAction, service.upload)
        self.switch_default = self.fields.single_field(
            SwitchDefaultSSHKeypairAction, service.switch_default
        )
