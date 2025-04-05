from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.groups.processors import GroupProcessors
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.users.processors import UserProcessors
from ai.backend.manager.services.vfolder.processors import (
    VFolderBaseProcessors,
    VFolderFileProcessors,
    VFolderInviteProcessors,
)


class Processors:
    domain: DomainProcessors
    group: GroupProcessors
    user: UserProcessors
    image: ImageProcessors
    container_registry: ContainerRegistryProcessors

    vfolder: VFolderBaseProcessors
    vfolder_invitation: VFolderInviteProcessors
    vfolder_file: VFolderFileProcessors

    def __init__(
        self,
        domain: DomainProcessors,
        group: GroupProcessors,
        user: UserProcessors,
        image: ImageProcessors,
        container_registry: ContainerRegistryProcessors,
        vfolder: VFolderBaseProcessors,
        vfolder_invite: VFolderInviteProcessors,
        vfolder_file: VFolderFileProcessors,
    ) -> None:
        self.domain = domain
        self.group = group
        self.user = user
        self.image = image
        self.container_registry = container_registry
        self.vfolder = vfolder
        self.vfolder_invitation = vfolder_invite
        self.vfolder_file = vfolder_file
