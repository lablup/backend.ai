from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.vfolder.processors import (
    VFolderBaseProcessors,
    VFolderFileProcessors,
    VFolderInviteProcessors,
)
from ai.backend.manager.services.vfolder.services import (
    VFolderFileService,
    VFolderInviteService,
    VFolderService,
)


class Processors:
    domain: DomainProcessors

    vfolder: VFolderBaseProcessors
    vfolder_invitation: VFolderInviteProcessors
    vfolder_file: VFolderFileProcessors

    def __init__(
        self,
        domain: DomainProcessors,
        vfolder_service: VFolderService,
        vfolder_invite_service: VFolderInviteService,
        vfolder_file_service: VFolderFileService,
    ):
        self.domain = domain

        self.vfolder = VFolderBaseProcessors(vfolder_service)
        self.vfolder_invitation = VFolderInviteProcessors(vfolder_invite_service)
        self.vfolder_file = VFolderFileProcessors(vfolder_file_service)
