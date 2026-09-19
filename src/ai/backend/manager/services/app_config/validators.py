"""Validators the app config processors append to the generic ops gates."""

from __future__ import annotations

from typing import Any, override

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.exception import UnreachableError, UserNotFound
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.domain.queriers import DomainQuerier
from ai.backend.manager.models.user.queriers import AuthorizingUserQuerier
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.app_config.actions.fragment.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)

__all__ = ("FragmentOwnerExistsValidator",)


class FragmentOwnerExistsValidator(ScopeActionValidator):
    """Refuse a fragment write whose owner names no domain or user, before the row goes in.

    The row carries no foreign key to its owner, so without this the missing owner is
    first noticed by the graph write behind the row — and answered as a server error.
    """

    _repository: OpsRepository[Any]

    def __init__(self, repository: OpsRepository[Any]) -> None:
        self._repository = repository

    @override
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        if not isinstance(action, BulkUpsertAppConfigFragmentsAction):
            raise UnreachableError(f"{type(action).__name__} is not a fragment write")
        owner = action.owner
        if owner.entity_type() == DomainEntityType():
            try:
                await self._repository.get(DomainQuerier(domain_id=DomainID(owner)))
            except EntityNotFoundError:
                raise DomainNotFound(extra_data={"domain_id": str(owner)}) from None
        elif owner.entity_type() == UserEntityType():
            try:
                await self._repository.get(AuthorizingUserQuerier(user_id=UserID(owner)))
            except EntityNotFoundError:
                raise UserNotFound(extra_data={"user_id": str(owner)}) from None
        else:
            raise UnreachableError(f"No app config scope owns a {owner.entity_type()}")
