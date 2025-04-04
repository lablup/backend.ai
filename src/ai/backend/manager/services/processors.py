from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.vfolder.processors import (
    VFolderBaseProcessors,
    VFolderFileProcessors,
    VFolderInviteProcessors,
)


class Processors:
    domain: DomainProcessors

    vfolder: VFolderBaseProcessors
    vfolder_invitation: VFolderInviteProcessors
    vfolder_file: VFolderFileProcessors

    def __init__(
        self,
        domain: DomainProcessors,
        vfolder: VFolderBaseProcessors,
        vfolder_invite: VFolderInviteProcessors,
        vfolder_file: VFolderFileProcessors,
    ) -> None:
        self.domain = domain

        self.vfolder = vfolder
        self.vfolder_invitation = vfolder_invite
        self.vfolder_file = vfolder_file
