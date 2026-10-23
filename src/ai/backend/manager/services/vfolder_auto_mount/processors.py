from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.services.vfolder_auto_mount.actions.bulk_get import (
    BulkGetVFolderAutoMountsAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.create import (
    CreateVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.delete import (
    DeleteVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.purge import (
    PurgeVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.restore import (
    RestoreVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.search import (
    SearchVFolderAutoMountsAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.update import (
    UpdateVFolderAutoMountAction,
)

__all__ = ("VFolderAutoMountProcessors",)


class VFolderAutoMountProcessors:
    """Every operation runs against ops; the domain keeps no service of its own."""

    bulk_get_ids: PartialBulkActionProcessor[BulkGetVFolderAutoMountsAction, VFolderAutoMountData]
    create: ScopeActionProcessor[
        CreateVFolderAutoMountAction, CreatedEntityOpsResult[VFolderAutoMountData]
    ]
    search: ScopeActionProcessor[
        SearchVFolderAutoMountsAction, ScopedBatchOpsResult[VFolderAutoMountData]
    ]
    update: SingleEntityActionProcessor[
        UpdateVFolderAutoMountAction, EntityOpsResult[VFolderAutoMountData]
    ]
    delete: SingleEntityActionProcessor[
        DeleteVFolderAutoMountAction, EntityOpsResult[VFolderAutoMountData]
    ]
    restore: SingleEntityActionProcessor[
        RestoreVFolderAutoMountAction, EntityOpsResult[VFolderAutoMountData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeVFolderAutoMountAction, EntityOpsResult[VFolderAutoMountData]
    ]

    def __init__(self, group: ProcessorGroup[VFolderAutoMountData]) -> None:
        self.bulk_get_ids = group.partial_bulk_get_ops(BulkGetVFolderAutoMountsAction)
        self.create = group.entity_create_ops(CreateVFolderAutoMountAction)
        self.search = group.scoped_search_ops(SearchVFolderAutoMountsAction)
        self.update = group.single_update_ops(UpdateVFolderAutoMountAction)
        self.delete = group.single_delete_ops(DeleteVFolderAutoMountAction)
        self.restore = group.single_restore_ops(RestoreVFolderAutoMountAction)
        self.purge = group.entity_purge_ops(PurgeVFolderAutoMountAction)
