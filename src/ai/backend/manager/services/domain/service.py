import logging

from sqlalchemy import exc as sa_exc

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
        try:
            if action.user_info.role == UserRole.SUPERADMIN:
                domain_data = await self._admin_repository.create_domain_force(action.creator)
            else:
                domain_data = await self._repository.create_domain_validated(action.creator)
            return CreateDomainActionResult(
                domain_data=domain_data,
                success=True,
                description="domain creation succeed",
            )
        except Exception as e:
            return CreateDomainActionResult(
                domain_data=None,
                success=False,
                description=f"domain creation failed: {str(e)}",
            )

    async def modify_domain(self, action: ModifyDomainAction) -> ModifyDomainActionResult:
        try:
            if action.user_info.role == UserRole.SUPERADMIN:
                domain_data = await self._admin_repository.modify_domain_force(
                    action.domain_name, action.modifier
                )
            else:
                domain_data = await self._repository.modify_domain_validated(
                    action.domain_name, action.modifier
                )
            if domain_data:
                return ModifyDomainActionResult(
                    domain_data=domain_data,
                    success=True,
                    description="domain modification succeed",
                )
            else:
                return ModifyDomainActionResult(
                    domain_data=None,
                    success=False,
                    description=f"no matching {action.domain_name}",
                )
        except Exception as e:
            return ModifyDomainActionResult(
                domain_data=None,
                success=False,
                description=f"domain modification failed: {str(e)}",
            )

    async def delete_domain(self, action: DeleteDomainAction) -> DeleteDomainActionResult:
        try:
            if action.user_info.role == UserRole.SUPERADMIN:
                success = await self._admin_repository.soft_delete_domain_force(action.name)
            else:
                success = await self._repository.soft_delete_domain_validated(action.name)
            if success:
                return DeleteDomainActionResult(
                    success=True,
                    description=f"domain {action.name} deleted successfully",
                )
            else:
                return DeleteDomainActionResult(
                    success=False, description=f"no matching {action.name}"
                )
        except Exception as e:
            return DeleteDomainActionResult(
                success=False, description=f"domain deletion failed: {str(e)}"
            )

    async def purge_domain(self, action: PurgeDomainAction) -> PurgeDomainActionResult:
        name = action.name

        try:
            if action.user_info.role == UserRole.SUPERADMIN:
                success = await self._admin_repository.purge_domain_force(name)
            else:
                success = await self._repository.purge_domain_validated(name)
            if success:
                return PurgeDomainActionResult(
                    success=True, description=f"domain {name} purged successfully"
                )
            else:
                return PurgeDomainActionResult(
                    success=False,
                    description=f"no matching {name} domain to purge",
                )
        except Exception as e:
            return PurgeDomainActionResult(
                success=False, description=f"domain purge failed: {str(e)}"
            )

    async def create_domain_node(
        self, action: CreateDomainNodeAction
    ) -> CreateDomainNodeActionResult:
        scaling_groups = action.scaling_groups

        try:
            if action.user_info.role == UserRole.SUPERADMIN:
                domain_data = (
                    await self._admin_repository.create_domain_node_with_permissions_force(
                        action.creator, action.user_info, scaling_groups
                    )
                )
            else:
                domain_data = await self._repository.create_domain_node_with_permissions(
                    action.creator, action.user_info, scaling_groups
                )
        except sa_exc.IntegrityError as e:
            raise ValueError(
                f"Cannot create the domain with given arguments. (arg:{action}, e:{str(e)})"
            )

        return CreateDomainNodeActionResult(
            domain_data=domain_data,
            success=True,
            description=f"domain {action.creator.name} created",
        )

    async def modify_domain_node(
        self, action: ModifyDomainNodeAction
    ) -> ModifyDomainNodeActionResult:
        domain_name = action.name

        if action.sgroups_to_add is not None and action.sgroups_to_remove is not None:
            if union := action.sgroups_to_add | action.sgroups_to_remove:
                raise ValueError(
                    "Should be no scaling group names included in both `sgroups_to_add` and `sgroups_to_remove` "
                    f"(sg:{union})."
                )

        try:
            if action.user_info.role == UserRole.SUPERADMIN:
                domain_data = (
                    await self._admin_repository.modify_domain_node_with_permissions_force(
                        domain_name,
                        action.modifier.fields_to_update(),
                        action.user_info,
                        action.sgroups_to_add,
                        action.sgroups_to_remove,
                    )
                )
            else:
                domain_data = await self._repository.modify_domain_node_with_permissions(
                    domain_name,
                    action.modifier.fields_to_update(),
                    action.user_info,
                    action.sgroups_to_add,
                    action.sgroups_to_remove,
                )
        except sa_exc.IntegrityError as e:
            raise ValueError(
                f"Cannot modify the domain with given arguments. (arg:{action}, e:{str(e)})"
            )
        if domain_data is None:
            raise ValueError(f"Domain not found (id:{domain_name})")

        return ModifyDomainNodeActionResult(
            domain_data=domain_data,
            success=True,
            description=f"domain {domain_name} modified",
        )
