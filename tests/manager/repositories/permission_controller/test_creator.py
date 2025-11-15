"""
Tests for RBACEntityCreator and RBACCreator functionality.
Tests the creator classes with real database operations.
"""

# from __future__ import annotations

# import uuid

# import pytest
# import sqlalchemy as sa
# from sqlalchemy.ext.asyncio import AsyncSession as SASession

# from ai.backend.manager.data.permission.id import ObjectId, ScopeId
# from ai.backend.manager.data.permission.types import EntityType, ScopeType
# from ai.backend.manager.models.rbac_models.association_scopes_entities import (
#     AssociationScopesEntitiesRow,
# )
# from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
# from ai.backend.manager.repositories.permission_controller.creator import (
#     RBACEntityCreateInput,
#     RBACEntityCreator,
# )