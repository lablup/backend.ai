from typing import NewType
from uuid import UUID

__all__ = ("VFolderUUID",)


# Named ``VFolderUUID`` (not ``VFolderID``) to avoid clashing with the
# existing composite ``VFolderID`` dataclass in ``common/types.py`` that
# pairs a ``quota_scope_id`` with a ``folder_id``. This alias represents
# the standalone UUID form used as the primary key of the vfolder row.
VFolderUUID = NewType("VFolderUUID", UUID)
