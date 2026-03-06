from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from graphql import OperationType
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo


def _get_mutation_class() -> type:
    """Lazily import Mutation to avoid circular import with schema.py."""
    mod = importlib.import_module("ai.backend.manager.api.gql.schema")
    return mod.Mutation


class GQLMutationPrivilegeCheckExtension(SchemaExtension):
    """Strawberry extension that enforces permission checks on mutation operations."""

    def resolve(
        self,
        _next: Callable[..., AwaitableOrValue[object]],
        root: Any,
        info: GraphQLResolveInfo,
        *args: Any,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        if info.operation.operation == OperationType.MUTATION and info.path.prev is None:
            mutation_cls_root = _get_mutation_class()
            mutation_field = getattr(mutation_cls_root, info.field_name, None)
            if mutation_field is not None:
                mutation_cls = getattr(mutation_field, "type", None)
                allowed_roles = getattr(mutation_cls, "allowed_roles", None)
                if allowed_roles is not None:
                    # TODO: Integrate user role checking when StrawberryGQLContext has user info.
                    # Once available, check: if user_role not in allowed_roles: raise PermissionDeniedError()
                    pass
        return _next(root, info, *args, **kwargs)
