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
from ai.backend.manager.services.ssh_key.actions.lookup_owner import (
    LookupBulkSSHKeypairOwnerAction,
    LookupSSHKeypairOwnerAction,
)
from ai.backend.manager.services.ssh_key.actions.search import ScopedSearchSSHKeypairsAction
from ai.backend.manager.services.ssh_key.actions.switch_default import (
    SwitchDefaultSSHKeyAction,
    SwitchDefaultSSHKeyActionResult,
)
from ai.backend.manager.services.ssh_key.actions.upload import (
    UploadSSHPublicKeyAction,
    UploadSSHPublicKeyActionResult,
)
from ai.backend.manager.services.ssh_key.service import SSHKeyService


class SSHKeyProcessors:
    """An SSH key is a field row of its user. ``upload`` names the user and runs through
    ``group``; the operations naming a key by its id run through ``fields``, where the
    owning user answers."""

    fields: LookupFieldGroup[SSHKeypairData]
    scoped_search: BulkActionProcessor[
        ScopedSearchSSHKeypairsAction, ScopedFieldsOpsResult[SSHKeypairData]
    ]
    upload: SingleEntityActionProcessor[UploadSSHPublicKeyAction, UploadSSHPublicKeyActionResult]
    switch_default: SingleFieldActionProcessor[
        SwitchDefaultSSHKeyAction, SwitchDefaultSSHKeyActionResult
    ]

    def __init__(self, group: ProcessorGroup[UserData], service: SSHKeyService) -> None:
        self.fields = group.field_group(
            FieldGroupMeta(SSHKeypairFieldType()),
            SSHKeypairData,
            LookupSSHKeypairOwnerAction,
            LookupBulkSSHKeypairOwnerAction,
        )
        self.scoped_search = self.fields.atomic_bulk_scoped_search_ops(
            ScopedSearchSSHKeypairsAction
        )
        self.upload = group.single_entity(UploadSSHPublicKeyAction, service.upload)
        self.switch_default = self.fields.single_field(
            SwitchDefaultSSHKeyAction, service.switch_default
        )
