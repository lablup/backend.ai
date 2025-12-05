import logging

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.domain.admin_repository import AdminDomainRepository
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.services.domain.actions.create_domain import (
    CreateDomainAction,
    CreateDomainActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain_node import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.delete_domain import (
    DeleteDomainAction,
    DeleteDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain import (
    ModifyDomainAction,
    ModifyDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain_node import (
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DomainService:
    _repository: DomainRepository
    _admin_repository: AdminDomainRepository

    def __init__(
        self,
        repository: DomainRepository,
        admin_repository: AdminDomainRepository,
    ) -> None:
        self._repository = repository
        self._admin_repository = admin_repository

    async def create_domain(self, action: CreateDomainAction) -> CreateDomainActionResult:
        domain_name_candidate = action.creator.name.strip()
        if domain_name_candidate == "" or len(domain_name_candidate) > 64:
            raise InvalidAPIParameters("Domain name cannot be empty or exceed 64 characters.")

        if action.user_info.role == UserRole.SUPERADMIN:
            domain_data = await self._admin_repository.create_domain_force(action.creator)
        else:
            domain_data = await self._repository.create_domain_validated(action.creator)
        return CreateDomainActionResult(
            domain_data=domain_data,
        )

    async def modify_domain(self, action: ModifyDomainAction) -> ModifyDomainActionResult:
        if action.user_info.role == UserRole.SUPERADMIN:
            domain_data = await self._admin_repository.modify_domain_force(
                action.domain_name, action.modifier
            )
        else:
            domain_data = await self._repository.modify_domain_validated(
                action.domain_name, action.modifier
            )
        return ModifyDomainActionResult(
            domain_data=domain_data,
        )

    async def delete_domain(self, action: DeleteDomainAction) -> DeleteDomainActionResult:
        if action.user_info.role == UserRole.SUPERADMIN:
            await self._admin_repository.soft_delete_domain_force(action.name)
        else:
            await self._repository.soft_delete_domain_validated(action.name)

        return DeleteDomainActionResult(
            name=action.name,
        )

    async def purge_domain(self, action: PurgeDomainAction) -> PurgeDomainActionResult:
        name = action.name

        if action.user_info.role == UserRole.SUPERADMIN:
            await self._admin_repository.purge_domain_force(name)
        else:
            await self._repository.purge_domain_validated(name)
        return PurgeDomainActionResult(
            name=name,
        )

    async def create_domain_node(
        self, action: CreateDomainNodeAction
    ) -> CreateDomainNodeActionResult:
        domain_name_candidate = action.creator.name.strip()
        if domain_name_candidate == "" or len(domain_name_candidate) > 64:
            raise InvalidAPIParameters("Domain name cannot be empty or exceed 64 characters.")

        scaling_groups = action.scaling_groups

        if action.user_info.role == UserRole.SUPERADMIN:
            domain_data = await self._admin_repository.create_domain_node_with_permissions_force(
                action.creator, action.user_info, scaling_groups
            )
        else:
            domain_data = await self._repository.create_domain_node_with_permissions(
                action.creator, action.user_info, scaling_groups
            )

        return CreateDomainNodeActionResult(
            domain_data=domain_data,
        )

    async def modify_domain_node(
        self, action: ModifyDomainNodeAction
    ) -> ModifyDomainNodeActionResult:
        domain_name = action.name

        if action.sgroups_to_add is not None and action.sgroups_to_remove is not None:
            if union := action.sgroups_to_add | action.sgroups_to_remove:
                raise InvalidAPIParameters(
                    "Should be no scaling group names included in both `sgroups_to_add` and `sgroups_to_remove` "
                    f"(sg:{union})."
                )

        if action.user_info.role == UserRole.SUPERADMIN:
            domain_data = await self._admin_repository.modify_domain_node_with_permissions_force(
                domain_name,
                action.modifier.fields_to_update(),
                action.user_info,
                action.sgroups_to_add,
                action.sgroups_to_remove,
            )
        else:
            domain_data = await self._repository.modify_domain_node_with_permissions(
                domain_name,
                action.modifier.fields_to_update(),
                action.user_info,
                action.sgroups_to_add,
                action.sgroups_to_remove,
            )
        return ModifyDomainNodeActionResult(
            domain_data=domain_data,
        )
