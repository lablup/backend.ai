from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Final

from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types.graphql import OperationType

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.errors.common import ServerFrozen

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GQLMutationUnfrozenRequiredExtension(SchemaExtension):
    """Blocks all mutation operations when the manager is frozen."""

    def on_execute(self) -> Iterator[None]:
        ctx = self.execution_context.context
        if (
            self.execution_context.operation_type == OperationType.MUTATION
            and ctx.manager_status == ManagerStatus.FROZEN
        ):
            raise ServerFrozen
        yield
